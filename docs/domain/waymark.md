# Waymark Domain

## Status

Provisional domain model for the first useful product slice. It turns the
[Waymark context reference](../../../management/references/products/waymark_context_reference.md)
into concrete language and rules without choosing an application framework,
payment provider, or storage technology.

## Product promise

Waymark gives one person a private place to record notes and timestamped facts,
then inspect summaries derived from those records. A paid subscription grants
access to that place; commercial state never becomes the source of truth for
the person's records.

## Ubiquitous language

| Term | Meaning |
| --- | --- |
| User | The person who owns and uses the private workspace. |
| Workspace | The user's private container for entries. There is exactly one per user in the first version. |
| Payer | The billing identity responsible for the user's subscription. It is the same person as the user in the first version, but is named separately because the responsibilities differ. |
| Note | A durable free-form entry recording an observation, thought, explanation, or reference. |
| Log entry | A durable entry recording that something happened at a particular time. |
| Entry | The common name for a note or log entry when their shared behavior matters. It is not a generic extension mechanism. |
| Subscription | The recurring commercial agreement for the single Waymark plan. |
| Billing period | The interval through which a successful payment funds access. |
| Entitlement | The time-bounded grant allowing the user to access their workspace. |
| Access state | A derived answer—`allowed` or `restricted`—for a user at a particular instant. It is not stored as an independent flag. |
| Metric snapshot | A reproducible, disposable summary derived from entries over a selected period. It is never an independent business fact. |

## Domain boundaries

### Recording

Recording owns the workspace and its durable entries. A note records text and
the instant it was created. A log entry records text and both the instant the
activity happened and the instant it was recorded. These instants may differ.

Entries remain durable when access is restricted. Restriction prevents use of
the workspace; it does not delete or rewrite what was recorded.

### Access and billing

Access and billing owns the subscription, payment outcomes, billing periods,
and entitlement lifecycle. Provider identifiers and webhook formats belong at
an adapter boundary and are not domain language.

The entitlement is evidence created from subscription facts. Access is allowed
only when an entitlement is effective at the instant being checked and is not
suspended. No separate `has_access` field may override those facts.

### Insights

Insights derives metric snapshots from notes and log entries. A snapshot can be
discarded and recomputed without losing business truth. The first snapshot is a
count of notes and log entries per day for a selected inclusive date range in
the user's timezone.

## Cardinality and ownership

For the first version:

```text
User (1) ── owns ── (1) Workspace
  │
  ├── represented by ── (1) Payer
  └── covered by ── (0..1) current Subscription

Workspace (1) ── contains ── (0..n) Entries
Subscription (1) ── produces ── (0..n) time-bounded Entitlements
Entries (0..n) ── project into ── (0..n) Metric Snapshots
```

Organizations, seats, shared workspaces, multiple plans, trials, credits,
coupons, and public entries are outside this model.

## Invariants

1. A user owns exactly one private workspace.
2. Only the workspace owner may read or write its entries.
3. Writing or reading entries requires access to be allowed at request time.
4. Every entry belongs to exactly one workspace and has an immutable identity.
5. A log entry's `happened_at` is explicit and may be earlier or later than its
   `recorded_at`; `recorded_at` is assigned by Waymark.
6. Commercial lifecycle changes never alter or delete entries.
7. There is at most one current subscription for a user.
8. An entitlement has a start and an exclusive end (`effective_from <= t <
   effective_until`).
9. Access is derived from entitlement and suspension facts for the instant in
   question.
10. A metric snapshot identifies its source range and calculation version and
    can always be recomputed from entries.

## Provisional commercial policy

These rules make the first slice testable. They are product decisions to
validate with real use, not payment-provider behavior.

- A successful initial payment activates the subscription and grants an
  entitlement through the end of the paid billing period.
- A failed renewal payment suspends the entitlement immediately. There is no
  grace period in the first version.
- A later successful recovery payment resumes the entitlement without changing
  its original period boundary unless the payment covers a new period.
- Cancellation schedules the subscription to end at the current paid period's
  boundary. Access remains allowed until that exclusive boundary.
- Reaching the period boundary without a successful renewal expires the
  entitlement and restricts access.
- An operator may record a payment correction, suspend an entitlement, or
  restore it. Every intervention must preserve the actor, reason, and time as a
  durable fact.

## Source facts and derived views

The first implementation should preserve these facts using names equivalent to
the following. The names describe domain meaning; they do not mandate event
sourcing.

### Durable facts

- `AccountCreated`
- `WorkspaceCreated`
- `NoteRecorded`
- `LogEntryRecorded`
- `SubscriptionRequested`
- `PaymentSucceeded`
- `PaymentFailed`
- `SubscriptionActivated`
- `CancellationScheduled`
- `EntitlementGranted`
- `EntitlementSuspended`
- `EntitlementRestored`
- `EntitlementExpired`
- `OperatorInterventionRecorded`

### Derived views

- current subscription state
- entitlement at an instant
- workspace access state
- daily entry counts for a selected period

Facts use stable Waymark identifiers and timestamps. External payment event and
customer identifiers are correlation data at the billing boundary; they must
not replace Waymark identities.

## First implementation slice

Build one vertical flow before adding more entry types or metrics:

1. Create a user, payer, and private workspace.
2. Request the single subscription.
3. Record a successful payment and grant a period-bounded entitlement.
4. Check access and record either a note or log entry.
5. Produce daily entry counts for a selected range.
6. Schedule cancellation and demonstrate access before and at the period end.

The application boundary initially needs these intentions:

- create account
- start subscription
- record payment outcome
- cancel subscription
- check workspace access
- record note
- record log entry
- get daily entry summary
- inspect account and subscription
- intervene in entitlement

## Acceptance scenarios

### Successful subscription grants access

Given a user without an entitlement, when the initial payment succeeds for a
billing period, then an entitlement covers that period and workspace access is
allowed during it.

### Failed renewal suspends access

Given an active entitlement, when its renewal payment fails, then the
entitlement is suspended and access is restricted immediately, while existing
entries remain unchanged.

### Recovered payment restores access

Given an entitlement suspended for payment failure, when recovery payment
succeeds, then the entitlement is restored and access is allowed for the
covered period.

### Cancellation honors the paid period

Given an active subscription paid through `2026-09-01T00:00:00Z`, when the user
cancels, then access remains allowed before that instant and is restricted at
that instant unless another entitlement covers it.

### Summary is reproducible

Given notes and log entries in a selected range, when the daily summary is
calculated more than once with the same calculation version and timezone, then
the same counts are returned without creating new business facts.

### Operator action is inspectable

Given a user whose entitlement is suspended incorrectly, when an operator
restores it, then access is allowed and inspection shows who intervened, when,
and why.

## Open discovery questions

- Whether notes and log entries remain distinct after a week of real use.
- Whether entries need projects or tags; neither exists in the first slice.
- Whether immediate suspension on payment failure is acceptable or a grace
  period is needed.
- Which timezone changes mean for historical daily summaries.
- Whether users need read-only export while access is restricted.
- Which operator actions are actually necessary beyond entitlement correction.

Resolve these through usage and recorded decisions before expanding the model.
