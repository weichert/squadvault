# Paste-Safe File Writes (v1.0)

This repo strongly prefers **paste-safe** file writes when creating or updating scripts, patchers, wrappers, or structured docs.

The canonical tool is `scripts/clipwrite.sh` (wraps `scripts/clipwrite.py`).

## Canonical Usage

~~~bash
bash scripts/clipwrite.sh path/to/file <<'EOF'
<exact content here>
EOF
~~~

Notes:
- `clipwrite` refuses to write an empty file.
- If the target file already matches stdin **exactly**, `clipwrite` is a **no-op**.
- Output is written UTF-8.

## When to Use

Use `clipwrite` whenever:
- creating or updating scripts
- writing patchers or wrappers
- authoring docs with structure
- copying content from ChatGPT, email, or web UI

## Anti-Patterns

❌ `cat > file` (especially for long/critical files)  
❌ editor paste for long scripts  
❌ partial heredocs  
❌ manual re-wrap “fixes” after the fact

## Guarantees

If it writes successfully:
- the file is complete
- encoding is UTF-8
- content is exactly what you intended
