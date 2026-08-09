# Entry Identity and Retry Safety

## Selection

- Runtime target: the existing Recording environment.
- Architecture: stable entry identity in durable facts and replayed entries.

## Contract

Every note and log entry has an immutable identity. Repeating a write with the
same identity and content returns the existing entry without appending another
entry fact. A conflicting retry is rejected.

## Deterministic test plan

- generated entries receive stable IDs;
- same-ID retries do not duplicate entries or facts;
- same-ID conflicting content is rejected;
- IDs and entry contents survive replay.

## Done criteria

Recording satisfies the identity invariant and can tolerate a retried command
after an uncertain network response.

## Out of scope

Entry editing, deletion, merges, imports, and cross-workspace identity.
