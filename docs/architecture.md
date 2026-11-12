# Architecture and scaffold decisions

Status: structure only. The functional design is in the shared plan.

The existing repository at `/home/fadhil/Projects/mars-return` is reused. The scaffold preserves the original plan's `server/`, `web/`, `shared/` and `data/` paths. No alternate worktree or second application was created. No dependencies, runtime modules or deployment have been installed.

Group A supplies prepared data and calculations. Group B consumes them in synchronized 2D/3D views and explanations. A3 and B1 share contract ownership. B3's assistant adapter remains under server/ even though B3 belongs to Group B, because provider credentials and trusted plan lookup belong server-side.

Actual code filenames in the group plans are future deliverables. README files preserve directory ownership in Git without pretending to be implemented modules. The shared contract is a draft prose design; generating a strict schema and fixtures is the next joint task.

Source downloads and bulk derived assets remain outside ordinary Git history. Small metadata and source records can be tracked. A reproducible demo-data package and startup process will be added during implementation.
