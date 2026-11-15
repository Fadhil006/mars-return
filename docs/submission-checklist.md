# Submission checklist — B1

Based on the official [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/). **Deadline: Sunday 15 November 2026, 11:59 p.m. Local Event time.** Only the last "Submit for Judging" counts; resubmitting before the deadline is allowed.

## Verified on 2026-11-15

- [x] `pytest server/tests`: 118 passed.
- [x] `python -m server.export_schema --check`: passed.
- [x] `cd web && npm ci && npm run typecheck && npm test && npm run build`: 32 tests passed, build succeeded.
- [x] Server started locally against the real CTX bundle (dataset `7e08b277f6761b7c`). Plan, brief and stress requests returned results; the planner rendered in Chromium.

## Required before submitting (team)

- [ ] **Demo:** a video of 30 seconds or less, or at most 7 slides including title and intro. Going over either limit makes the project ineligible for Global Awards. Use English, or English subtitles on a video. Slides must name the team, its members and the challenge. Upload it publicly (YouTube, Drive, etc.) and test the link in a private window.
- [ ] **Project link:** make `https://github.com/Fadhil006/mars-return` public and test it in a private window.
- [ ] **Form fields:** name, summary (1500 characters at most), details, SI checkboxes, NASA Data links, other data and tools.
- [ ] **AI disclosure:** described in the README under "Use of AI tools". Any AI-generated image or video in the demo needs a visible watermark. Confirm whether `docs/design/concepts/files/*.png` were AI-generated; if so, watermark them or say so beside them.
- [ ] **No minors:** no images, video or voice of anyone under 18 in the demo or project.
- [ ] **Registration:** all six members confirmed at the same Local Event.
- [ ] **Checkboxes:** tick "Agree to Terms and Conditions" and "Confirm All Work is Original", then click "Submit for Judging" and wait for the confirmation banner.

## Not done (optional)

- Hosted deployment: none. The public repository and the demo are the judged links.
- License: no `LICENSE` file. The team should choose one.
