# Verification report

Command:

```sh
python3 -m unittest discover -s tests -v
```

Result: **2/2 tests passing**.

The tests cover added/removed declaration detection, Python and TypeScript
symbols, consumer versus test-path grouping, JSON output, strict-mode exit
code, and the non-execution boundary using a fixture marker command.

A disposable explicit-patch smoke run also produced a JSON receipt.
