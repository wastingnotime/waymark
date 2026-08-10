# Waymark Simulation

This is Waymark's MRL simulation project. It is the place where the product
model is extracted, mapped, refined, and released before technology adapters
become authoritative.

The simulation is one evolving deterministic environment. It currently covers
the first subscription-backed workspace slice: activation, recording, payment
failure, recovery, and access expiry.
The cancellation edge also supports an explicit effective boundary and an
explainable `cancelled` access decision.

Run the pure simulation tests from the repository root:

```bash
pytest sandboxes/simulation/tests
```

When the shared WNT MRL Runtime is available, run the runtime adapter with:

```bash
mrl-simulation supervise --scenario-factory app.simulation.mrl_runtime_scenario:create_simulation
```

The runtime adapter is an integration boundary for supervision and evidence;
the simulation behavior remains repository-owned and runtime-independent.
