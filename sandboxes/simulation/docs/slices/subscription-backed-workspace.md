# Subscription-Backed Workspace

## Selection

- Implementation pack: WNT Python event-sourced simulation.
- Runtime target: deterministic headless simulation plus WNT MRL Runtime
  adapter.
- Architecture: one evolving environment with append-only facts and derived
  access state.

## Discovery scope

Validate the first useful flow from account creation through recording,
payment failure, recovery, cancellation/expiry, and summary derivation. Keep
provider-specific payment behavior outside the model.

## Use-case contract

The environment supports: create account, activate a paid period, record a
note, record a log entry, fail payment, recover payment, cancel, check access,
and summarize daily entries.

## Required ports

- controlled simulation clock;
- deterministic identifier source;
- append-only fact history;
- payment provider fake with success/failure outcomes;
- observation sink for semantic runtime evidence.

## Deterministic test plan

- activation allows workspace access;
- notes and logs are accepted while entitled;
- payment failure restricts new writes but preserves existing facts;
- recovery restores access before period end;
- period end restricts access at the exclusive boundary;
- daily summaries can be recomputed identically;
- repeated provider delivery does not duplicate facts.

## Scenario

Start at `2026-09-01T00:00:00Z`. Create the account, activate a seven-day
period, record one note, fail renewal, attempt a restricted write, recover
payment, record one log entry, then reach the period boundary. Emit semantic
observations for each intention, command, fact, access decision, and invariant.

## Done criteria

The scenario is deterministic for a fixed seed, all invariants pass, existing
entries survive access restriction, and the runtime adapter can expose the run
through the common WNT launcher.

## Out of scope

Multiple plans, trials, grace periods, provider webhooks, organizations, tags,
projects, exports, and AI interpretation.
