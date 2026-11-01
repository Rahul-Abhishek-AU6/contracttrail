# Research: contract drift after AI-assisted refactors

Researched: 2026-11-02

## Signal

AI-assisted coding is normalizing, while validation and review have become the
bottleneck. Stack Overflow's 2025 Developer Survey reports that 84% of
developers use or plan to use AI tools; 66% cite outputs that are "almost
right" as a frustration, and 45% say debugging AI-generated code takes more
time. It also reports more respondents distrust AI accuracy (46%) than trust
it (33%). [Stack Overflow 2025 survey](https://survey.stackoverflow.co/2025/)

The 2025 Go Developer Survey identifies non-functional code as the primary AI
tool problem for 53% of respondents. [Go survey results](https://go.dev/blog/survey2025)
Recent industry survey reporting likewise points to manual review (52%) and
security testing (51%) as major bottlenecks for AI-generated code.
[Black Duck, March 2026](https://www.blackduck.com/resources/analyst-reports/state-of-ai-powered-software-development.html)

## Candidate problems considered

| Candidate | Demand | Why not selected |
|---|---|---|
| Generic AI code reviewer | High | Requires a hosted model/API or duplicates mature tools. |
| Test-impact reporter | High | Already covered by the factory's TestSignal release. |
| Instruction-file inventory | Emerging | Already covered by the factory's RuleTrace release. |
| Contract drift receipt for refactors | High, narrow | A local static MVP can expose changed declarations and likely internal consumers before a reviewer hunts manually. |

## Selected problem: ContractTrail

An AI-assisted refactor can update a Python or TypeScript declaration while
leaving call sites, tests, docs, or exports behind. Reviewers must infer the
blast radius from a diff and search separately. **ContractTrail** will be a
standard-library Python CLI that:

1. reads a Git diff (or explicit patch),
2. identifies added/removed declaration lines for conservative Python and
   TypeScript patterns,
3. searches repository text for probable symbol consumers, and
4. emits a Markdown/JSON receipt grouped into declaration changes, likely
   consumers, tests, and limitations.

It will never claim type correctness, parse every language, execute code, or
replace a compiler/test suite. It instead creates an auditable review starting
point from local files only.

## Free/local feasibility

Python 3's standard library can parse patch hunks, scan UTF-8 source files,
and render Markdown/JSON. Git is optional when `--patch` is supplied. No
model, API key, network access, package install, telemetry, or paid service is
needed.

## MVP acceptance criteria

- Detect changed `def` / `class` declarations in Python and `function`,
  `class`, and exported `const` declarations in JS/TS.
- Locate likely textual consumers while excluding the changed declaration file
  line itself.
- Label test-path consumers separately.
- Produce stable Markdown and JSON receipts.
- Return a non-zero strict status when a changed declaration has no discovered
  test consumer, while avoiding a claim that tests are absent.
