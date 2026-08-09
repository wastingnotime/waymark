# Operator Inspection and Intervention

## Selection

- Runtime target: the existing deterministic Waymark simulation and WNT
  Runtime adapter.
- Architecture: an operations intention over the existing access facts; no
  separate operations service.

## Contract

An operator can inspect a user's access reason, identity, workspace, and entry
count. An operator may restore an entitlement suspended for payment failure.
Every intervention records the operator, reason, and simulation time.

## Deterministic test plan

- inspection reports `payment_failed` while payment failure is active;
- restore requires a non-empty actor and reason;
- restore records a durable operator intervention fact;
- restore returns access to allowed;
- inspection does not mutate entry or payment facts.

## Done criteria

Inspection and restoration extend the shared first-slice environment, emit
semantic observations, and preserve an auditable event history.

## Out of scope

Roles, approval workflows, operator accounts, bulk actions, and support-ticket
integration.
