# Backend verification

Run `.venv/bin/python -m pytest server/tests` from the repository root. Synthetic known-answer tests cover preparation/coordinates, route optimality and exclusions, mission budgets, API/schema behavior, trusted evaluation records, acquisition checksums and packaging. `.venv/bin/python -m scripts.validate_demo` separately checks prepared real terrain and the original DEM. Do not confuse synthetic algorithm checks with real-world scientific validation; remaining alignment and deployment gates are in `docs/validation.md`.
