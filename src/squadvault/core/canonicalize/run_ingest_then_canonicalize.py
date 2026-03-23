"""DEPRECATED — canonical location is squadvault.ops.run_ingest_then_canonicalize.

This shim will be removed in a future version. Update imports to:
    from squadvault.ops.run_ingest_then_canonicalize import ...
"""
import warnings as _w
_w.warn(
    "squadvault.core.canonicalize.run_ingest_then_canonicalize is deprecated. "
    "Use squadvault.ops.run_ingest_then_canonicalize.",
    DeprecationWarning, stacklevel=2,
)
from squadvault.ops.run_ingest_then_canonicalize import *  # noqa: F401,F403
from squadvault.ops.run_ingest_then_canonicalize import main, parse_args  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
