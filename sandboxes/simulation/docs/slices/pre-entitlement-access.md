# Pre-Entitlement Access

## Selection

- Runtime target: access decisions before the first paid period.
- Architecture: derived access state over absent entitlement facts.

## Contract

After account creation but before entitlement activation, workspace access is
restricted with reason `no_entitlement`. No entry command can succeed in this
state.

## Done criteria

The runtime first-flow scenario observes the restricted pre-entitlement state.

## Out of scope

Free plans, trials, previews, and read-only onboarding access.
