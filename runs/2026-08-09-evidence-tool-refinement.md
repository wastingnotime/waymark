# Waymark Evidence Tool Refinement Check

Date: 2026-08-09

## Finding closed

The evidence runner previously returned success regardless of invariant state.
It now exits non-zero when any invariant result is false, while preserving the
JSONL log for inspection and replay.

## Evidence

```text
run_first_slice.py
wrote 48 observations to JSONL

mrl-simulation replay
consumed the JSONL evidence successfully

pytest -q
25 passed
```

## Decision

Evidence generation is now suitable as a local validation gate. Deliberate
failure-injection scenarios remain future evaluation work.
