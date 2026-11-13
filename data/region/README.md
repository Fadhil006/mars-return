# Prepared region bundle — A1 and A3

Runtime products: manifest.json, imagery.webp, elevation.json, slope.json, mask.json and science-stops.json. Reproduce the real Jezero bundle with `.venv/bin/python -m scripts.prepare_demo` from the repository root. Bulk generated layers are ignored; the manifest, source records and hypothetical observation points are tracked. Missing layers are not automatically replaced with synthetic data. See `docs/data-method.md` and `docs/validation.md` for processing, checksums, packaging and limits.
