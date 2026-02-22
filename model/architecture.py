"""PyTorch decoder-only transformer architecture used for language modeling."""

from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint

from model.config import ModelConfig


class RMSNorm(nn.Module):
    """Root mean square normalization layer."""

    def __init__(self, hidden_size: int, eps: float = 1e-6) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(hidden_size))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        variance = x.float().pow(2).mean(dim=-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return self.weight * x.type_as(self.weight)


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate half of head features for RoPE."""
    x1 = x[..., ::2]
    x2 = x[..., 1::2]
    rotated = torch.stack((-x2, x1), dim=-1)
    return rotated.flatten(start_dim=-2)


class RotaryEmbedding(nn.Module):
    """Rotary positional embedding cache and application helpers."""

    def __init__(self, dim: int, max_position: int, base: float = 10_000.0) -> None:
        super().__init__()
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        positions = torch.arange(max_position, dtype=torch.float32)
        freqs = torch.outer(positions, inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        self.register_buffer("cos_cache", emb.cos(), persistent=False)
        self.register_buffer("sin_cache", emb.sin(), persistent=False)

    def apply(self, q: torch.Tensor, k: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        seq_len = q.size(-2)
        cos = self.cos_cache[:seq_len].unsqueeze(0).unsqueeze(0).to(dtype=q.dtype, device=q.device)
        sin = self.sin_cache[:seq_len].unsqueeze(0).unsqueeze(0).to(dtype=q.dtype, device=q.device)
        q_out = (q * cos) + (rotate_half(q) * sin)
        k_out = (k * cos) + (rotate_half(k) * sin)
        return q_out, k_out


class SelfAttention(nn.Module):
    """Multi-head causal self-attention using FlashAttention via SDPA."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.num_heads = config.num_heads
        self.head_dim = config.head_dim
        self.hidden_size = config.hidden_size
        self.dropout = config.dropout

        self.q_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.k_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.v_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.o_proj = nn.Linear(config.hidden_size, config.hidden_size, bias=config.use_bias)
        self.rope = RotaryEmbedding(
            dim=self.head_dim,
            max_position=config.context_length,
            base=config.rope_theta,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size, seq_len, _ = x.shape

        q = self.q_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        q, k = self.rope.apply(q, k)

        attn_output = F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=None,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=True,
        )
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.hidden_size)
        return self.o_proj(attn_output)


class SwiGLUFeedForward(nn.Module):
    """SwiGLU feed-forward network."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.ffn_size, bias=config.use_bias)
        self.up_proj = nn.Linear(config.hidden_size, config.ffn_size, bias=config.use_bias)
        self.down_proj = nn.Linear(config.ffn_size, config.hidden_size, bias=config.use_bias)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.silu(self.gate_proj(x)) * self.up_proj(x)
        x = self.down_proj(x)
        return self.dropout(x)


class TransformerBlock(nn.Module):
    """Pre-norm transformer block with attention and SwiGLU FFN."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.attn_norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.ffn_norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.attn = SelfAttention(config)
        self.ffn = SwiGLUFeedForward(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.attn_norm(x))
        x = x + self.ffn(self.ffn_norm(x))
        return x


class TransformerModel(nn.Module):
    """Decoder-only transformer language model."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.config = config
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.blocks = nn.ModuleList([TransformerBlock(config) for _ in range(config.num_layers)])
        self.final_norm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        self.lm_head.weight = self.embed_tokens.weight

    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        x = self.embed_tokens(input_ids)

        for block in self.blocks:
            if self.config.gradient_checkpointing and self.training:
                x = checkpoint(block, x, use_reentrant=False)
            else:
                x = block(x)

        x = self.final_norm(x)
        logits = self.lm_head(x)
        output: dict[str, torch.Tensor] = {"logits": logits}

        if labels is not None:
            loss = F.cross_entropy(
                logits.view(-1, logits.size(-1)),
                labels.view(-1),
                ignore_index=-100,
            )
            output["loss"] = loss
        return output
