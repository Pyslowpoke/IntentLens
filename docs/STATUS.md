# Current status

Updated 2026-10-09. Development build; not a fully accepted release.

- Public GitHub Pages demo is published, with fixed synthetic data and rule-based calculations; it is not the full AI workbench.
- Latest GitHub CI at b3dec47 passed. Real DeepSeek model tests use synthetic inputs and retain prompts, output and timing separately.
- Current changes: diagnostics/clarification prompt constraints, explicit consent before aggregate decision payloads, UI and trial feedback entry.
- Docker on a clean machine, real-user retention and complete release acceptance remain unverified. Project LICENSE still requires an owner decision.
- Historical test counts are not current acceptance guarantees. See docs/TEST-EVIDENCE.md for required evidence.

## Historical snapshot (2026-09-27, superseded)

# Status

Updated 2026-09-27 (Asia/Shanghai). **Runnable development delivery; not yet a fully accepted V1 release.** No existing project was overwritten. Next.js generated its own apps/web/AGENTS.md during development; its version-matched docs were read.

## Verified facts

- Next.js 16.3.6 / React 19.3.0 / TypeScript / Tailwind / shadcn-style Radix button UI; production build and typecheck pass. Vitest: 3 passing tests.
- FastAPI/Pydantic API, SQLite project/run/revision store, Parquet snapshots, separate subprocess worker, SSE events, cancellation/retry/timeouts and compare-and-swap stale-result protection are implemented and exercised.
- Full Python suite: **43 passed**, zero skips; includes actual PostgreSQL/MySQL/SQLite connections and database-level write rejection. Subsequent contract/mapping and self-contained bundle changes: 14 targeted tests passed. See JUnit evidence.
- Browser E2E: import synthetic sales → recommendation → actual Plotly rendering → title/color/sort/filter/undo → PNG download → reload → 6 revisions; passed in 45.4 s on the final rerun before the additive chart mapping field. Dedicated recorded demo also exercises the current app.
- Excel sheet/header selection, missing values, dates/formula cache warnings, GB18030, duplicate headers, invalid numeric correction, independent ratio known answers and incomplete-month warning tested.
- Seven adapters produced real artifacts. Four core engines × three themes exported exact 1000×560 PNGs. Chinese text/negative values/annotations/legends/margins were opened and visually inspected. Additional chart-type tests passed. Specialized outputs include 100k density and viewport recompute, WGS84 point map and formatted table.
- Fixed 10k/100k/1m benchmarks ran, three repetitions each; original JSON and measured browser latency preserved. No performance superiority claim.
- Official portable PostgreSQL 17.11 / MySQL 8.4.11 run on loopback test ports 55432 / 53306, with synthetic seeds and restricted reader roles. They are not Windows services. The ignored .local directory contains test binaries/data. An ASCII junction under LOCALAPPDATA points there because PostgreSQL initdb failed on the original Chinese path.
- Native app currently runs at http://127.0.0.1:3000 with API :8000 and an independent worker. Data survives API/worker process restart. `scripts/start.ps1` provides a repeatable local launch.

## Remaining mandatory acceptance / release blockers

1. **Clean Docker Compose build/run and no-network container export verification are unexecuted:** this host has no Docker executable/runtime. Configuration, fonts and browser installation are supplied, but must be proven in a clean Docker environment before V1 acceptance. No system-wide Docker installation/restart was attempted.
2. **Live model quality and model-generated NL-to-SQL/edits are untested:** no MODEL / MODEL_API_KEY was configured. Three wire protocols and authentication/rate-limit/server errors have mock tests. `scripts/verify_live_model.py` runs an explicit opt-in three-attempt synthetic test when the operator configures credentials; it keeps all failures. Do not paste keys into chat.
3. **Container typography still needs clean-environment confirmation.** Local visual QA now includes all four core engines × three themes, long Chinese labels, percentage/negative-value formatting, annotations, legend spacing and exact output sizes. Representative local scenario 11 checks pass; no claim is made for arbitrary fonts or every possible dense chart.
4. User must choose the project license before publication. Dependency inventories identify LGPL/MPL/CC-BY obligations; no public release, cloud resource or promotional message was created.

## Next concrete action

Run `docker compose up --build` in a Docker-capable clean environment, run the same browser and export tests against it, and check worker egress/credentials/resource limits and Chinese fonts. With optional server-side model configuration, run all three live adapter tests and retain their attempt records. Continue from this file; do not recreate the project.
