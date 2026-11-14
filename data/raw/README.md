# Original source downloads — A1

Local input files are ignored by Git. `scripts.prepare_demo` downloads/reuses the registered CTX elevation and imagery GeoTIFFs and verifies their SHA-256 values. Product IDs, URLs, temporal information, checksums and attribution are in `data/sources/`. Do not edit originals. Existing files with incorrect checksums cause a clear failure rather than being silently overwritten.
