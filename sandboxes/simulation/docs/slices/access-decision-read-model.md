# Access Decision Read Model

The access boundary exposes a small, explainable read model for each check:

- `allowed` says whether the workspace can be used now.
- `reason` identifies the boundary that decided the result.
- `subscription_status` identifies the derived commercial lifecycle state.

Unauthorized users are denied without changing state. Payment failure produces
`allowed=false`, `reason=payment_failed`, and `subscription_status=past_due`.
The boolean `access_check` API remains compatible while emitting this richer
decision payload for operators and downstream projections.
