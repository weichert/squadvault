from pathlib import Path

TARGET = Path("docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md")

def main() -> None:
    if not TARGET.exists():
        raise RuntimeError(f"Missing required doc: {TARGET}")

if __name__ == "__main__":
    main()
