"""Train a SentencePiece tokenizer from cleaned text corpora."""

import argparse
from pathlib import Path
from typing import Iterable, Sequence

import sentencepiece as spm

SPECIAL_TOKENS: tuple[str, ...] = (
    "<|system|>",
    "<|user|>",
    "<|assistant|>",
    "<|tool|>",
)


def discover_input_files(data_dir: Path) -> list[Path]:
    """Collect text-like files recursively from the input directory."""
    supported_suffixes = {".txt", ".jsonl", ".md"}
    return sorted(
        path
        for path in data_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in supported_suffixes
    )


def validate_vocab_size(vocab_size: int) -> None:
    """Validate vocab size against the requested 32k-64k range."""
    if not 32_000 <= vocab_size <= 65_536:
        raise ValueError("vocab_size must be between 32,000 and 65,536.")


def train_sentencepiece(
    input_files: Sequence[Path],
    output_prefix: str,
    vocab_size: int,
    character_coverage: float,
) -> None:
    """Run SentencePiece BPE training with project special tokens."""
    if not input_files:
        raise FileNotFoundError("No training files found for tokenizer training.")

    validate_vocab_size(vocab_size)
    spm.SentencePieceTrainer.train(
        input=",".join(str(path) for path in input_files),
        model_prefix=output_prefix,
        model_type="bpe",
        vocab_size=vocab_size,
        character_coverage=character_coverage,
        shuffle_input_sentence=True,
        split_digits=True,
        byte_fallback=True,
        unk_id=0,
        bos_id=1,
        eos_id=2,
        pad_id=3,
        user_defined_symbols=list(SPECIAL_TOKENS),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser for tokenizer training."""
    parser = argparse.ArgumentParser(description="Train a SentencePiece tokenizer.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/cleaned"),
        help="Directory containing cleaned training text files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tokenizer"),
        help="Directory where tokenizer model/vocab files are written.",
    )
    parser.add_argument(
        "--model-prefix",
        type=str,
        default="spm_48k",
        help="Prefix name for generated tokenizer files.",
    )
    parser.add_argument(
        "--vocab-size",
        type=int,
        default=49_152,
        help="Vocabulary size in the 32k-64k range.",
    )
    parser.add_argument(
        "--character-coverage",
        type=float,
        default=0.9995,
        help="Character coverage for SentencePiece training.",
    )
    return parser


def main() -> None:
    """Entry point for tokenizer training."""
    parser = build_arg_parser()
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_files = discover_input_files(args.data_dir)
    output_prefix = str(args.output_dir / args.model_prefix)
    train_sentencepiece(
        input_files=input_files,
        output_prefix=output_prefix,
        vocab_size=args.vocab_size,
        character_coverage=args.character_coverage,
    )


if __name__ == "__main__":
    main()
