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
9. Simulation facts are append-only, ordered, and replayable; provider outcomes
   enter through a deterministic fake boundary.
10. Operator inspection is read-only; operator restoration is an explicit,
    attributed intervention over a suspended entitlement.
11. Daily summaries group recorded instants by the caller's explicit IANA
    timezone; entry facts remain timezone-neutral.
12. A successful payment after expiry creates a new entitlement period and does
    not reopen the expired interval.
13. Live state can be rehydrated from the ordered fact history without emitting
    new facts.
14. Payment correlation IDs make repeated provider delivery idempotent at the
    simulation boundary.
15. Log entries preserve caller-supplied activity time separately from
    Waymark-assigned recording time; summaries currently group by recording
    time.
16. Notes and logs have immutable identities, and same-identity retries do not
    append duplicate entry facts.
17. Operator inspection is a read-only projection containing enough lifecycle
    state to explain the current access decision.
18. Daily summary observations identify their calculation version; the version
    is projection metadata, not a durable business fact.
19. Only the workspace owner may access or record entries; unauthorized actors
    receive an explanatory rejection without domain mutation.

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

The next selected slice is documented in
`docs/slices/operator-inspection.md`.

The timezone summary slice is documented in
`docs/slices/timezone-summaries.md`.

The renewal slice is documented in `docs/slices/renewal-after-expiry.md`.

The replay slice is documented in `docs/slices/event-replay.md`.

The payment idempotency slice is documented in
`docs/slices/payment-idempotency.md`.

The log timestamp slice is documented in `docs/slices/log-timestamps.md`.

The entry identity slice is documented in
`docs/slices/entry-identity.md`.

The operator inspection read model is documented in
`docs/slices/operator-inspection-read-model.md`.

The summary versioning slice is documented in
`docs/slices/summary-versioning.md`.

The workspace ownership slice is documented in
`docs/slices/workspace-ownership.md`.
