# MARS RETURN: one container serving the API and the built planner (used by Render, see render.yaml).
# The terrain is prepared during the build from the USGS source files (~432 MB, checksum-verified);
# only the ~1 MB prepared bundle is kept in the final image.

FROM node:24-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
# Optional platform packages (TypeScript 7, rolldown) are skipped silently when a download fails: retry, then check.
RUN npm ci --no-audit --no-fund --fetch-retries=5 --fetch-retry-maxtimeout=120000 \
 && ls node_modules/@typescript/ | grep -q "typescript-linux-" \
 || { echo "TypeScript native compiler missing after npm ci" >&2; exit 1; }
COPY web/ ./
RUN npm run build

FROM python:3.12-slim AS terrain
WORKDIR /app
# rasterio's wheel bundles GDAL but links the system libexpat, which the slim image lacks.
RUN apt-get update && apt-get install -y --no-install-recommends libexpat1 && rm -rf /var/lib/apt/lists/*
COPY server/requirements.lock server/
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r server/requirements.lock
COPY server/ server/
COPY scripts/ scripts/
COPY data/sources/ data/sources/
COPY data/region/science-stops.json data/region/rover-traverse.json data/region/
RUN python -m scripts.prepare_demo && rm -rf data/raw/*

FROM python:3.12-slim
WORKDIR /app
# The running API needs neither the raster tools nor the test tools, so it installs the runtime subset only.
COPY server/requirements-runtime.lock server/
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r server/requirements-runtime.lock && useradd --create-home app
COPY server/ server/
COPY --from=terrain /app/data/region/ data/region/
COPY --from=web /app/web/dist/ web/dist/
USER app
ENV PYTHONUNBUFFERED=1 PORT=8000
EXPOSE 8000
# One worker: saved plans live in process memory (see CLAUDE.md).
CMD ["sh", "-c", "exec python -m uvicorn server.api:app --host 0.0.0.0 --port ${PORT} --workers 1"]
