"""AutoLink — intelligence-routing substrate.

DAI is the executive intelligence that lives inside AutoLink. AutoLink itself
contains:

- AutoLD   — router               (ld_router.py)
- AutoLCE  — context engine       (lce_context.py)
- AutoLM   — memory layer         (lm_memory.py)
- AutoLIP  — integration points   (lip_integration.py)

Execution engines (AutoOD/AutoClink) live in engines.py.

Security layers (AutoTrust, AutoLS) are NOT implemented yet; AutoLIP exposes
clean precheck/postcheck hooks so they can be added later.
"""

from .ld_router import AutoLD
from .lce_context import AutoLCE
from .lm_memory import AutoLM
from .lip_integration import AutoLIP
from .engines import AutoOD, AutoClink

__all__ = ["AutoLD", "AutoLCE", "AutoLM", "AutoLIP", "AutoOD", "AutoClink"]
