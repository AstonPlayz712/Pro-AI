"""AutoLink (AL) — environment layer.

AL is the only component that can resolve vault refs, talk to sources, and
enforce permission/quota/health policies. DAI never reaches the outside
world except through an ALManager.
"""

from .manager import ALManager

__all__ = ["ALManager"]
