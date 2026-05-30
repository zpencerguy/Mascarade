# Mascarade Simulator

This repository starts from the imported Codex project brief in
`docs/mascarade_simulator_codex_plan.md`.

The first implementation is intentionally small:

- a deterministic rules engine for regular 4 to 13 player Mascarade;
- dynamic ontology/config loading from editable JSON;
- a power registry so character behavior can be added as small skills;
- a random bot and CLI for smoke-running games;
- focused tests for challenge resolution, character powers, setup, and end states.

## Quick Start

```bash
PYTHONPATH=src python3 -m unittest discover
python3 -m mascarade_sim single --players 6 --seed 1 --verbose
python3 -m mascarade_sim run --players 6 --games 1000 --seed 42
```

## Ontology

The dynamic project knowledge lives in `config/ontology.json`. It defines:

- character schemas and constraints;
- setup profiles by player count;
- action and event schemas;
- skill bindings from character names to Python power handlers.

The engine validates the ontology at load time and dispatches character powers
through the registry in `mascarade_sim.characters`.

## Known Rulebook Gaps

The exact official basic character configuration for every player count still
needs verification from the physical rulebook table. The default config is
editable and currently uses a conservative development setup for 6 players.
