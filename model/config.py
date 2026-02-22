"""Configuration objects for decoder-only transformer language models."""

from dataclasses import dataclass


@dataclass(slots=True)
class ModelConfig:
    """Hyperparameter container for a decoder-only transformer."""

    num_layers: int
    hidden_size: int
    num_heads: int
    ffn_size: int
    vocab_size: int
    context_length: int
    dropout: float = 0.0
    rms_norm_eps: float = 1e-6
    rope_theta: float = 10_000.0
    use_bias: bool = False
    gradient_checkpointing: bool = True

    def __post_init__(self) -> None:
        if self.hidden_size % self.num_heads != 0:
            raise ValueError("hidden_size must be divisible by num_heads.")
        if min(
            self.num_layers,
            self.hidden_size,
            self.num_heads,
            self.ffn_size,
            self.vocab_size,
            self.context_length,
        ) <= 0:
            raise ValueError("All core config dimensions must be positive integers.")

    @property
    def head_dim(self) -> int:
        """Dimension per attention head."""
        return self.hidden_size // self.num_heads


def build_1b_config() -> ModelConfig:
    """Create a practical ~1B-parameter decoder-only model configuration."""
    return ModelConfig(
        num_layers=24,
        hidden_size=2048,
        num_heads=16,
        ffn_size=5504,
        vocab_size=49_152,
        context_length=4096,
        dropout=0.0,
        rms_norm_eps=1e-6,
        rope_theta=10_000.0,
        use_bias=False,
        gradient_checkpointing=True,
    )
