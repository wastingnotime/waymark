# Cancellation Idempotency

## Selection

- Runtime target: the existing subscription cancellation boundary.
- Architecture: one scheduled cancellation per current paid period.

## Contract

Repeating cancellation with the same current subscription is harmless. It
preserves one `CancellationScheduled` fact and the original effective boundary
while emitting an informational duplicate notice.

## Done criteria

Cancellation retries are safe before the paid-period boundary.

## Out of scope

Undo cancellation, plan changes, refunds, and cancellation surveys.
