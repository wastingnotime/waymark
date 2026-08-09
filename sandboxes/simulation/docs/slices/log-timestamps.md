# Log Timestamps

## Selection

- Runtime target: the existing Recording and Insights behavior.
- Architecture: preserve activity time and recording time on the durable entry.

## Contract

A log entry carries `happened_at`, chosen by the caller, and `recorded_at`,
assigned from the controlled simulation clock. They may differ. Daily summaries
group by `recorded_at`; activity-time analytics remain future work.

## Deterministic test plan

- a log can describe an earlier activity;
- both timestamps survive replay;
- summary grouping remains based on recorded time;
- note entries continue to have only their recorded time.

## Done criteria

The runtime scenario and replay preserve the two timestamps without conflating
activity history with capture history.

## Out of scope

Editing timestamps, inferred activity time, timezone conversion of happened-at,
and activity-time trend metrics.
