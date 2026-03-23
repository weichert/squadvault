"""DEPRECATED — canonical location is squadvault.core.eal.consume_v1.

This shim will be removed in a future version. Update imports to:
    from squadvault.core.eal.consume_v1 import ...
"""
import warnings as _w
_w.warn(
    "squadvault.eal.consume_v1 is deprecated. "
    "Use squadvault.core.eal.consume_v1.",
    DeprecationWarning, stacklevel=2,
)
from squadvault.core.eal.consume_v1 import *  # noqa: F401,F403
from squadvault.core.eal.consume_v1 import EALDirectivesV1, load_eal_directives_v1  # noqa: F401
