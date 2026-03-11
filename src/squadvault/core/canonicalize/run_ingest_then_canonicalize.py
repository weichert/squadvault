"""Re-export shim — canonical location is squadvault.ops.run_ingest_then_canonicalize"""
from squadvault.ops.run_ingest_then_canonicalize import *  # noqa: F401,F403
from squadvault.ops.run_ingest_then_canonicalize import main, parse_args  # noqa: F401

if __name__ == "__main__":
    raise SystemExit(main())
