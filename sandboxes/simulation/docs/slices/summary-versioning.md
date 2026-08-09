# Summary Calculation Versioning

## Selection

- Runtime target: the existing Insights projection.
- Architecture: version metadata on derived observations, not durable entry
  facts.

## Contract

Every daily summary observation includes a stable calculation version. The
version identifies the grouping/calculation semantics used for that result and
allows later implementations to compare or recompute projections explicitly.

## Done criteria

The runtime observation and unit tests expose the current version without
turning derived summaries into source-of-truth events.

## Out of scope

Persisted snapshot storage, migration tooling, and multiple concurrent summary
algorithms.
