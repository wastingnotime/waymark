# Waymark

## Retirement

Retired at the owner's request on 2026-10-13 and preserved as an archived
reference. Active development has stopped. The provisional domain model,
Python source, deterministic simulation, tests, and run evidence are preserved.
See the [retirement record](https://github.com/wastingnotime/waymark/blob/main/docs/decommission.md).

## Historical Purpose

Waymark is a quiet, private workspace for recording what happens and seeing
what emerges over time.

The product domain is being established before delivery technology is chosen.
Start with [the domain model](docs/domain/waymark.md) for the current language,
rules, and first implementation slice.

The model must be refined through the [simulation project](sandboxes/simulation/README.md)
before the Python package is treated as a technology implementation.

## Development

The first slice is a framework-free Python domain package. Run its deterministic
tests with:

```bash
pytest
```
