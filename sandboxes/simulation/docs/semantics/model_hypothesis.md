# Model Hypothesis

## Current vocabulary

User, payer, private workspace, note, log entry, subscription, billing period,
entitlement, access decision, and daily metric summary.

## Boundaries

- Recording owns durable notes and log entries.
- Access owns subscription, payment outcomes, entitlement periods, and access
  decisions.
- Insights derives daily counts from recorded entries and is not a source of
  truth.

## Current rules

1. A successful payment creates an entitlement for a bounded billing period.
2. A payment failure suspends the current entitlement immediately.
3. A recovery before period end restores the suspended entitlement.
4. A recovery after period end creates a new period and does not reopen the old
   period.
5. Cancellation preserves access through the paid period boundary.
6. At the exclusive entitlement boundary, access is restricted.
7. Notes and logs remain durable across commercial state changes.
8. Daily summaries are recomputable projections, not facts.

## Open questions

- Is immediate payment-failure suspension acceptable, or is a grace period
  needed?
- Do notes and logs remain distinct after real use?
- Which operator interventions are required beyond entitlement correction?
- Which timezone semantics make daily summaries useful?

## Candidate slices

The first selected slice is documented in
`docs/slices/subscription-backed-workspace.md`. Further slices must extend this
shared environment rather than creating separate simulations.
