# Plan: ContractTrail

## Interface

```sh
python3 contracttrail.py scan /path/to/repository
python3 contracttrail.py scan . --patch change.patch --json receipt.json
python3 contracttrail.py scan . --strict
```

`scan` uses `git diff --unified=0` when no patch is passed. The patch parser
collects removed and added declaration lines, then scans tracked-looking text
files in the target tree for word-boundary references to each changed symbol.

## Conservative rules

- Support only recognizable Python `def`/`class` and JavaScript/TypeScript
  `function`/`class`/`const` declaration syntax.
- Never evaluate, import, execute, or modify repository content.
- Exclude the changed declaration line itself from consumer results.
- Label paths with test-like components (`test`, `tests`, `spec`, `__tests__`)
  as tests; all other hits are likely consumers.
- Report an absence as "no test-path reference found", not proof that no test
  covers the change.

## Verification

Fixture tests will cover declaration detection, reference grouping, explicit
patch input, JSON output, strict exit behavior, and non-execution of a marker
command stored in fixture source.
