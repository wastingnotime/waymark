# Waymark Pre-Entitlement Access Refinement Check

Date: 2026-08-09

## Finding closed

Pre-entitlement coverage now proves both the `no_entitlement` access decision
and rejection of entry recording before activation.

## Evidence

```text
pytest -q
37 passed

SimulationRunner
run_id: waymark-first-slice
observations: 84
invariant:
  pre_entitlement_is_restricted: passed
```

## Decision

The workspace remains non-writable until an entitlement is effective.
