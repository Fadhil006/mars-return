# Architecture and scaffold decisions

Status: Group A backend implemented; Group B browser/assistant remains scaffold work. The shared plans describe the full team scope; actual verification is recorded in `docs/validation.md`.

The existing repository at `/home/fadhil/Projects/mars-return` is reused, preserving `server/`, `web/`, `shared/` and `data/`. The Python service uses pinned dependencies and prepared local terrain. No database, login, or alternate application was added.

Group A supplies prepared data and calculations. Group B consumes them in synchronized 2D/3D views and explanations. A3 and B1 share contract ownership. B3's assistant adapter remains under server/ even though B3 belongs to Group B, because provider credentials and trusted plan lookup belong server-side.

Runtime Pydantic models generate the shared JSON Schema; explicitly synthetic fixtures exercise the real API against invented grids. Real endpoints never return these fixtures as a fallback. Routing uses containing-cell centers in the prepared Mars frame, eight-neighbor A*, common exclusions and explicit mission legs.

Source downloads and bulk derived assets remain outside ordinary Git history. Source records, region metadata and hypothetical observation-point definitions are tracked. `scripts.prepare_demo` verifies source checksums and versions all prepared layers and destination metadata; `scripts.package_region` packages validated runtime assets. Saved evaluations live in bounded process memory, so the service runs with one worker and requires recalculation after restart.
