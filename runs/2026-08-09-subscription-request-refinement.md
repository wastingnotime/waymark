# Waymark Subscription Request Refinement Check

Date: 2026-08-09

## Finding closed

Activation now guarantees a subscription request exists. Direct simulation
callers that begin at activation receive an explicit implicit subscription
request, while the runtime scenario continues to exercise the named request
and duplicate-request path.

## Evidence

```text
pytest -q
32 passed

SimulationRunner
run_id: waymark-first-slice
observations: 69
invariant:
  subscription_request_is_unique: passed
```

## Decision

The activation boundary cannot produce an entitlement without subscription
request state. Multiple plans remain outside scope.
