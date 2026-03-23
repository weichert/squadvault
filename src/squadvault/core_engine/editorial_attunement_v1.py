"""DEPRECATED — canonical location is squadvault.core.eal.editorial_attunement_v1.

This shim will be removed in a future version. Update imports to:
    from squadvault.core.eal.editorial_attunement_v1 import ...
"""
import warnings as _w
_w.warn(
    "squadvault.core_engine.editorial_attunement_v1 is deprecated. "
    "Use squadvault.core.eal.editorial_attunement_v1.",
    DeprecationWarning, stacklevel=2,
)
from squadvault.core.eal.editorial_attunement_v1 import *  # noqa: F401,F403
from squadvault.core.eal.editorial_attunement_v1 import EALMeta, evaluate_editorial_attunement_v1  # noqa: F401
