#!/usr/bin/env python3
"""ContractTrail: local, conservative review receipts for changed declarations."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

DECLARATION = re.compile(
    r"^(?:\s*(?:export\s+)?(?:async\s+)?function\s+|\s*(?:export\s+)?(?:const|class)\s+|\s*(?:async\s+)?def\s+|\s*class\s+)([A-Za-z_$][\w$]*)"
)
TEXT_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".md"}


@dataclass(frozen=True)
class Change:
    path: str
    symbol: str
    kind: str
    line: str


@dataclass(frozen=True)
class Reference:
    path: str
    line: int
    category: str
    text: str


def read_patch(root: Path, patch_path: str | None) -> str:
    if patch_path:
        return Path(patch_path).read_text(encoding="utf-8")
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--unified=0"],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return result.stdout


def changes_from_patch(patch: str) -> list[Change]:
    path = None
    changes: list[Change] = []
    for raw in patch.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            continue
        if not path or raw.startswith(("+++", "---", "@@")) or not raw[:1] in {"+", "-"}:
            continue
        match = DECLARATION.match(raw[1:])
        if match:
            changes.append(Change(path, match.group(1), "added" if raw[0] == "+" else "removed", raw[1:].strip()))
    return changes


def is_test_path(path: Path) -> bool:
    lowered = [part.lower() for part in path.parts]
    name = path.name.lower()
    return any(part in {"test", "tests", "spec", "__tests__"} for part in lowered) or name.startswith("test_") or name.endswith((".test.py", ".spec.py", ".test.ts", ".spec.ts"))


def references(root: Path, change: Change) -> list[Reference]:
    found: list[Reference] = []
    needle = re.compile(rf"\b{re.escape(change.symbol)}\b")
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file() or candidate.suffix.lower() not in TEXT_SUFFIXES or ".git" in candidate.parts:
            continue
        rel = candidate.relative_to(root).as_posix()
        try:
            lines = candidate.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, text in enumerate(lines, 1):
            if rel == change.path and DECLARATION.match(text) and change.symbol in text:
                continue
            if needle.search(text):
                category = "test" if is_test_path(candidate.relative_to(root)) else "consumer"
                found.append(Reference(rel, number, category, text.strip()[:160]))
    return found


def make_receipt(root: Path, patch: str) -> dict:
    changes = changes_from_patch(patch)
    rows = []
    for change in changes:
        refs = references(root, change)
        rows.append({"change": asdict(change), "references": [asdict(item) for item in refs]})
    return {"tool": "ContractTrail", "root": str(root), "declaration_changes": rows,
            "limits": ["Textual references are review leads, not type checking.",
                       "No test-path reference found does not prove absent coverage.",
                       "Only conservative Python and JS/TS declaration patterns are recognized."]}


def markdown(receipt: dict) -> str:
    rows = receipt["declaration_changes"]
    lines = ["# ContractTrail receipt", f"- Declaration changes: {len(rows)}", ""]
    for row in rows:
        change = row["change"]
        refs = row["references"]
        tests = sum(ref["category"] == "test" for ref in refs)
        consumers = sum(ref["category"] == "consumer" for ref in refs)
        lines.append(f"## {change['kind']} `{change['symbol']}` — `{change['path']}`")
        lines.append(f"- Likely consumers: {consumers}; test-path references: {tests}")
        if not refs:
            lines.append("- No local textual references found.")
        for ref in refs:
            lines.append(f"- **{ref['category']}** `{ref['path']}:{ref['line']}` — {ref['text']}")
        lines.append("")
    lines.extend(["## Limits", *[f"- {item}" for item in receipt["limits"]], ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan")
    scan.add_argument("root", type=Path)
    scan.add_argument("--patch")
    scan.add_argument("--json", dest="json_path")
    scan.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = make_receipt(args.root.resolve(), read_patch(args.root.resolve(), args.patch))
    except (OSError, RuntimeError) as error:
        print(f"contracttrail: {error}", file=sys.stderr)
        return 1
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(markdown(receipt))
    if args.strict and any(not any(ref["category"] == "test" for ref in row["references"])
                           for row in receipt["declaration_changes"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
