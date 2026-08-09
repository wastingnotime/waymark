# Timezone-Aware Summaries

## Selection

- Runtime target: the existing deterministic simulation and Insights
  projection.
- Architecture: a projection parameter, not a new source of truth.

## Contract

Daily summaries accept an absolute instant range and an IANA timezone name.
Entries are filtered by their recorded instants, then grouped by the local
calendar date in that timezone. The timezone is returned with the projection
observation.

## Deterministic test plan

- UTC remains the default;
- an entry near midnight is grouped by its requested local date;
- repeated calculation with the same timezone is identical;
- an unknown timezone is rejected explicitly.

## Done criteria

The summary projection remains recomputable and no timezone-specific state is
stored in durable entry facts.

## Out of scope

User preference persistence, timezone migration, locale-specific formatting,
and calendar systems other than the IANA/Gregorian combination.
