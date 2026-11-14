# Development fixtures — A3 with B1

Generate with `.venv/bin/python -m scripts.generate_fixtures` from the repository root. Each file wraps an explicit `synthetic` label, request, endpoint, HTTP status, and actual service response from an invented grid. `success` includes a slope-cost tradeoff; `identical-routes` is flat terrain. Other cases cover over-budget, no-path, invalid input, missing data and return-only rehearsal. Never present these as NASA observations. Fixture plan IDs are stable labels, not live lookup IDs.
