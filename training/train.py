"""Training script for decoder-only next-token prediction."""

import argparse
import logging
import math
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR
from torch.utils.data import DataLoader, Dataset

from model.architecture import TransformerModel
from model.config import build_1b_config


class TokenChunkDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Create next-token chunks from contiguous token ID tensors."""

    def __init__(self, file_paths: list[Path], block_size: int, split: str) -> None:
        if not file_paths:
            raise FileNotFoundError(f"No token files found for split '{split}'.")

        token_tensors = [torch.load(path, map_location="cpu").long().view(-1) for path in file_paths]
        self.tokens = torch.cat(token_tensors, dim=0)
        self.block_size = block_size
        self.sequence_count = (self.tokens.numel() - 1) // self.block_size
        if self.sequence_count <= 0:
            raise ValueError(
                f"Not enough tokens for split '{split}'. Need at least block_size + 1 tokens."
            )

    def __len__(self) -> int:
        return self.sequence_count

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        start = index * self.block_size
        end = start + self.block_size + 1
        chunk = self.tokens[start:end]
        input_ids = chunk[:-1]
        labels = chunk[1:]
        return input_ids, labels


@dataclass(slots=True)
class TrainArgs:
    """Runtime arguments for model training."""

    data_dir: Path
    output_dir: Path
    batch_size: int
    eval_batch_size: int
    num_epochs: int
    lr: float
    weight_decay: float
    warmup_steps: int
    log_interval: int
    eval_interval: int
    checkpoint_interval: int
    grad_clip: float


class Trainer:
    """Next-token prediction trainer with mixed precision and checkpointing."""

    def __init__(self, args: TrainArgs) -> None:
        self.args = args
        self.args.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.config = build_1b_config()
        self.model = TransformerModel(self.config).to(self.device)

        self.optimizer = AdamW(
            self.model.parameters(),
            lr=args.lr,
            weight_decay=args.weight_decay,
            betas=(0.9, 0.95),
            eps=1e-8,
        )

        train_files, val_files = self._discover_data_files(args.data_dir)
        self.train_loader = DataLoader(
            TokenChunkDataset(train_files, self.config.context_length, split="train"),
            batch_size=args.batch_size,
            shuffle=True,
            drop_last=True,
            num_workers=0,
            pin_memory=torch.cuda.is_available(),
        )
        self.val_loader = DataLoader(
            TokenChunkDataset(val_files, self.config.context_length, split="val"),
            batch_size=args.eval_batch_size,
            shuffle=False,
            drop_last=False,
            num_workers=0,
            pin_memory=torch.cuda.is_available(),
        )

        total_steps = args.num_epochs * len(self.train_loader)
        self.scheduler = LambdaLR(
            self.optimizer,
            lr_lambda=self._build_warmup_cosine_lambda(total_steps, args.warmup_steps),
        )

        self.global_step = 0
        self.best_val_loss = float("inf")

    @staticmethod
    def _discover_data_files(data_dir: Path) -> tuple[list[Path], list[Path]]:
        train_files = sorted((data_dir / "train").glob("*.pt"))
        val_files = sorted((data_dir / "val").glob("*.pt"))
        if not train_files or not val_files:
            raise FileNotFoundError(
                "Expected tokenized files in data/tokenized/train/*.pt and data/tokenized/val/*.pt"
            )
        return train_files, val_files

    @staticmethod
    def _build_warmup_cosine_lambda(total_steps: int, warmup_steps: int):
        def lr_lambda(step: int) -> float:
            if step < warmup_steps:
                return float(step + 1) / float(max(1, warmup_steps))
            progress = float(step - warmup_steps) / float(max(1, total_steps - warmup_steps))
            return max(0.1, 0.5 * (1.0 + math.cos(math.pi * progress)))

        return lr_lambda

    def _save_checkpoint(self, name: str, val_loss: float) -> None:
        checkpoint_path = self.args.output_dir / name
        torch.save(
            {
                "model": self.model.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "scheduler": self.scheduler.state_dict(),
                "global_step": self.global_step,
                "val_loss": val_loss,
            },
            checkpoint_path,
        )
        logging.info("Saved checkpoint: %s", checkpoint_path)

    @torch.no_grad()
    def validate(self) -> float:
        """Run validation loop and return mean loss."""
        self.model.eval()
        losses: list[float] = []

        for input_ids, labels in self.val_loader:
            input_ids = input_ids.to(self.device, non_blocking=True)
            labels = labels.to(self.device, non_blocking=True)

            with torch.autocast(device_type=self.device.type, dtype=torch.bfloat16, enabled=self.device.type == "cuda"):
                output = self.model(input_ids=input_ids, labels=labels)
                losses.append(float(output["loss"].item()))

        self.model.train()
        mean_loss = sum(losses) / max(1, len(losses))
        logging.info("Validation | step=%d | loss=%.4f", self.global_step, mean_loss)
        return mean_loss

    def train(self) -> None:
        """Run multi-epoch training with logging, validation, and checkpoints."""
        self.model.train()

        for epoch in range(1, self.args.num_epochs + 1):
            for input_ids, labels in self.train_loader:
                self.global_step += 1
                input_ids = input_ids.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                self.optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type=self.device.type, dtype=torch.bfloat16, enabled=self.device.type == "cuda"):
                    output = self.model(input_ids=input_ids, labels=labels)
                    loss = output["loss"]

                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.args.grad_clip)
                self.optimizer.step()
                self.scheduler.step()

                if self.global_step % self.args.log_interval == 0:
                    learning_rate = self.optimizer.param_groups[0]["lr"]
                    logging.info(
                        "Train | epoch=%d | step=%d | loss=%.4f | lr=%.6e",
                        epoch,
                        self.global_step,
                        float(loss.item()),
                        learning_rate,
                    )

                if self.global_step % self.args.eval_interval == 0:
                    val_loss = self.validate()
                    if val_loss < self.best_val_loss:
                        self.best_val_loss = val_loss
                        self._save_checkpoint("best.pt", val_loss)

                if self.global_step % self.args.checkpoint_interval == 0:
                    self._save_checkpoint(f"step_{self.global_step}.pt", val_loss=float("nan"))

            logging.info("Completed epoch %d/%d", epoch, self.args.num_epochs)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for training script CLI."""
    parser = argparse.ArgumentParser(description="Train a decoder-only language model.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/tokenized"))
    parser.add_argument("--output-dir", type=Path, default=Path("checkpoints"))
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--eval-batch-size", type=int, default=2)
    parser.add_argument("--num-epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--warmup-steps", type=int, default=100)
    parser.add_argument("--log-interval", type=int, default=10)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--checkpoint-interval", type=int, default=250)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    return parser


def main() -> None:
    """Entry point for model training."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    parser = build_arg_parser()
    namespace = parser.parse_args()
    args = TrainArgs(
        data_dir=namespace.data_dir,
        output_dir=namespace.output_dir,
        batch_size=namespace.batch_size,
        eval_batch_size=namespace.eval_batch_size,
        num_epochs=namespace.num_epochs,
        lr=namespace.lr,
        weight_decay=namespace.weight_decay,
        warmup_steps=namespace.warmup_steps,
        log_interval=namespace.log_interval,
        eval_interval=namespace.eval_interval,
        checkpoint_interval=namespace.checkpoint_interval,
        grad_clip=namespace.grad_clip,
    )

    trainer = Trainer(args)
    trainer.train()


if __name__ == "__main__":
    main()
