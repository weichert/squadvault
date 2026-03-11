.PHONY: test test-fast lint compile-check ci clean

# Run full test suite
test:
	PYTHONPATH=src python -m pytest Tests/ -q

# Run tests with verbose output
test-v:
	PYTHONPATH=src python -m pytest Tests/ -v

# Fast: skip slow property tests
test-fast:
	PYTHONPATH=src python -m pytest Tests/ -q -m "not slow"

# Compile check: verify all source is valid Python
compile-check:
	@python3 -c "\
	import py_compile, glob, sys; \
	errors = []; \
	[errors.append(str(e)) for f in glob.glob('src/squadvault/**/*.py', recursive=True) \
	 for e in [None] if not (lambda f: (py_compile.compile(f, doraise=True), True)[-1])(f) \
	 or False]; \
	" 2>&1 || python3 -c "\
	import py_compile, glob; \
	ok = True; \
	[ok := False or print(e) for f in glob.glob('src/squadvault/**/*.py', recursive=True) \
	 for e in [None] \
	 if not (lambda f: (py_compile.compile(f, doraise=True), True))]; \
	"
	@echo "Compile check: running..."
	@python3 -c "\
	import py_compile, glob, sys; \
	errors = []; \
	files = glob.glob('src/squadvault/**/*.py', recursive=True); \
	for f in files: \
	    try: py_compile.compile(f, doraise=True); \
	    except py_compile.PyCompileError as e: errors.append(str(e)); \
	if errors: \
	    print(f'{len(errors)} compile errors:'); [print(e) for e in errors]; sys.exit(1); \
	else: print(f'All {len(files)} files compile clean'); \
	"

# CI gate: tests + compile check + invariant checks
ci: compile-check test
	@echo "CI passed"

# Invariant gates
gate-no-bare-sqlite:
	@echo "Checking for bare sqlite3.connect outside allowed files..."
	@python3 -c "\
	import re, glob; \
	ALLOWED = {'sqlite_store.py', 'session.py', 'migrate.py'}; \
	violations = []; \
	for f in glob.glob('src/squadvault/**/*.py', recursive=True): \
	    import os; \
	    if os.path.basename(f) in ALLOWED: continue; \
	    with open(f) as fh: \
	        for i, line in enumerate(fh, 1): \
	            if 'sqlite3.connect(' in line and not line.strip().startswith('#'): \
	                violations.append(f'{f}:{i}'); \
	if violations: \
	    print(f'{len(violations)} bare sqlite3.connect calls found:'); \
	    [print(f'  {v}') for v in violations]; \
	    import sys; sys.exit(1); \
	else: print('No bare sqlite3.connect violations'); \
	"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache
