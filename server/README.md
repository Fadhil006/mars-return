# Group A service

Python 3.11+; dependency lock verified on Python 3.14/Linux. From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r server/requirements.lock
.venv/bin/python -m pytest server/tests
.venv/bin/python -m server.export_schema --check
```

`pyproject.toml` lists direct dependencies; `requirements.lock` pins the tested environment including test tools. Run modules from the repository root, not from `server/`.

A1 owns preprocessing and coordinates; A2 routing and mission arithmetic; A3 API, validation and evidence lookup. B3 owns the assistant/model adapter. Real-data preparation and service launch instructions are added as those checkpoints are verified. Synthetic tests are never evidence of actual Mars terrain accuracy.
