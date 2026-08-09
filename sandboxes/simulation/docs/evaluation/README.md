# Simulation Evaluation

The repository-owned headless tool emits the current scenario's observation
log as JSONL. Run it with the shared runtime on the import path:

```bash
PYTHONPATH=/home/henrique/.wnt/runtime/mrl:sandboxes/simulation/src \
  python3 sandboxes/simulation/tools/run_first_slice.py \
  --output runs/waymark-first-slice.jsonl
```

Inspect or replay the resulting evidence with the common launcher:

```bash
mrl-simulation inspect runs/waymark-first-slice.jsonl
mrl-simulation replay runs/waymark-first-slice.jsonl
```

Generated JSONL evidence is intentionally not committed by default; durable
validation receipts belong in `runs/` as Markdown summaries.
