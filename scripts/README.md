# Project automation

Run from the repository root with the installed `.venv`:

- `python -m scripts.prepare_demo`: download/reuse checksum-verified real CTX inputs, prepare the documented Jezero grid, and finalize versioned source/scenario metadata.
- `python -m scripts.validate_demo`: check real-data scenarios, returned geometry, source elevation and event reset; write `docs/validation-results.json`.
- `python -m scripts.package_region --region-dir data/region --output PATH.tar.gz`: validate/package six runtime assets, refuse overwrite, print SHA-256. Output parent must exist.
- `python -m scripts.generate_fixtures`: regenerate explicitly synthetic API development fixtures.
- `python -m server.export_schema [--check]`: generate/check the shared contract against runtime models.

The first command downloads about 450 MB; subsequent validation is offline. See `server/README.md` for exact `.venv/bin/python` commands and `docs/validation.md` for observed results. Frontend/deployment packaging remains B2's work.
