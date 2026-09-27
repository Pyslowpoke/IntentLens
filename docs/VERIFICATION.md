# Verification record — 2026-09-27

All facts below refer to commands executed on the current Windows host unless explicitly marked unexecuted. Final release status: **development delivery, V1 not fully accepted**.

## Environment and setup

Workspace: E:/桌面/star. Node 24.19.0; pnpm 11.25.0; Python 3.12.14; uv 0.12.19. Next 16.3.6 and React 19.3.0 were resolved from the package registry and locked. Python packages are locked in uv.lock; no architecture was replaced because of installation trouble.

`uv sync` initially stalled downloading scientific wheels. The exact locked llvmlite, vl-convert and Playwright wheels were downloaded from their files.pythonhosted.org URLs and SHA-256 verified with `scripts/verify_downloads.py`; installed via `uv pip install --no-deps`, then the rest via `uv sync --frozen --inexact --no-install-package llvmlite --no-install-package vl-convert-python --no-install-package playwright`. This is an installation workaround, not a dependency substitution. Standard clean installs use `uv sync --frozen`.

`pnpm install`, asset bundling, Chromium installation, sample generation and schema export executed. Windows Chromium headed executable had a side-by-side configuration error; the adapter now locates Playwright's functioning headless shell, also used by browser tests. Chinese font initialization was fixed to occur after Matplotlib theme selection.

## Executed checks

| Command | Actual result | Evidence |
|---|---|---|
| `pnpm typecheck` | pass | TypeScript completed without errors |
| `pnpm build` | pass | Next production build, static `/` and not-found routes |
| `pnpm test` | 3 pass | formatting/missing-value display and accessible disabled button |
| `.venv/Scripts/python.exe -m pytest -q --junitxml=docs/evidence/all-tests.xml` | **43 pass**, zero skips, 62.60 s | [JUnit](evidence/all-tests.xml) |
| `pytest tests/test_core.py tests/test_engines.py` after additive chart mapping/bundle changes | 14 pass | [Targeted JUnit](evidence/final-contract-check.xml) |
| `pnpm e2e` | 1 pass, 45.4 s | apps/web/playwright-report/index.html; screenshots below |
| `python -m scripts.render_gallery` | all requested gallery paths generated | [Gallery manifest](evidence/gallery/manifest.json), engine folders |
| `python -m scripts.visual_qa` | 12 exact 1000×560 PNG checks | [Theme manifest](evidence/themes/manifest.json) |
| `python -m scripts.long_label_qa` | four core engines, wrapped Chinese labels, exact 1200×700 exports | [Long-label manifest](evidence/long-labels/manifest.json) |
| `python -m scripts.verify_bundle` | default ZIP excludes data; explicit synthetic-data ZIP executed independently and rendered a 1000×560 PNG | [Reproduction evidence](evidence/bundle-verification.txt) |
| `python -m scripts.benchmark` | all 10k/100k/1m cases executed, 3 repeats | [Measured JSON](evidence/benchmark/results.json), [interpretation/budgets](PERFORMANCE.md) |
| `node scripts/capture_demo.mjs` | real recorded workflow with timing records | [Browser timings](evidence/browser-timings.json), evidence/video/*.webm |
| `python -m piplicenses ...`, `pnpm licenses list --json` | inventories generated | [License review](THIRD_PARTY.md) |
| `docker compose version` | unavailable: command not found | [Environment evidence](evidence/docker-check.txt) |

Two non-failing upstream deprecation warnings remain: Starlette's httpx TestClient adapter and Seaborn's Matplotlib boxplot orientation argument. A Windows malformed system font warning occurs in vl-convert; inspected exports use functioning Chinese font fallback. These warnings were not suppressed to turn a failure into a pass.

## Twelve required scenarios

| # | Scenario | Evidence and result |
|---:|---|---|
| 1 | Chinese multisheet Excel, dates/nulls | `test_excel_and_csv`: selects 中文销售, header row 2, retains all 4 rows; two null cached metrics; formula cache warning. **Pass** |
| 2 | CSV encoding/duplicate headers/invalid numbers | GB18030 fixture rejects wrong encoding; stable f1/f2/f3 retain duplicate 金额 names; invalid numeric cast explicitly rejects. **Pass** |
| 3 | Simple mean vs overall ratio | Independent answer: (0.5+0.9)/2 = **0.7**, (1+90)/(2+100) = **91/102**. Separate operations/interpretations. **Pass** |
| 4 | Incomplete month | Jan 300 vs partial Feb 50 fixture; actual observed range and incomplete-month warning asserted, no whole-month decline claim. **Pass** |
| 5 | Five natural-language edits | Browser and demo: title, blue, descending, filter 地区=华东, undo. Six immutable revisions. Worker known-answer style test keeps [100,200]; filter fixture returns 华东=100. **Pass in rule mode** |
| 6 | Late old task after replacing data | Real subprocess running while project changes dataset; run finishes stale, new head remains null and new dataset has one row. `test_late_real_worker_cannot_replace_new_dataset`. **Pass** |
| 7 | Four core engines and same numbers | Actual Plotly/Matplotlib/Altair/ECharts generation and exports; shared input [400,200,-50] unchanged. Gallery, 12-theme exact-size outputs and additional basic-chart tests. **Pass for implemented scope** |
| 8 | Three real databases and read-only behavior | SQLite existing file plus portable PostgreSQL/MySQL with fixed seeds; East 400, West 200; direct DB DELETE rejected. No mocks. **Pass** |
| 9 | Density/geo/KPI | Datashader 10k known count, narrowed viewport count lower; gallery 100k density. GeoPandas+offline pydeck WGS84 points and PNG. plottable numeric table and vector/image exports. **Pass for narrow paths** |
| 10 | Save/restart/history; cancel/fail/timeout | Real subprocess timeout/retry, running cancel, stale finish and cache tests; recreated API clients restore state; actual API/worker restarted and saved heads remained. Interrupted-job recovery explicitly fails runs for retry. **Pass** |
| 11 | Chinese text, labels, legend, margin, dimensions | Core charts, all three themes, specialty images and long Chinese labels opened visually; overlap/size/font issues fixed. 12 theme PNGs exactly 1000×560, long-label outputs exactly 1200×700, percentage and negative values retained. **Pass for the local representative suite**; clean-container font/export verification remains pending under M8. |
| 12 | No key demo / bad-key feedback | Default visibly labeled rule mode exercised by E2E; all three adapter 401/403/429/500 handling implemented (401/429/500 tested), secrets excluded. **Pass for rule/protocol path; real model inference untested** |

## Real database provisioning evidence

No Docker was available, so official portable distributions were used without system service installation:

- [PostgreSQL Windows binaries](https://www.postgresql.org/download/windows/), official EDB 17.11 binary ZIP. `initdb -U postgres -A trust --encoding=UTF8 --locale=C`, `pg_ctl ... -p 55432 -h 127.0.0.1`, `createdb workbench_test`, seed `infra/postgres.sql`. A project-local fixture is reached through an ASCII junction to avoid the observed initdb UTF-8 path failure. Trust bootstrap is for synthetic local fixtures only; the application test uses the restricted reader, not postgres.
- [MySQL 8.4 official ZIP](https://dev.mysql.com/downloads/mysql/8.4.html), version 8.4.11, vendor MD5 `2e833921898a9a030ea6bfe81bd811bc`, actual checksum matched. `mysqld --initialize-insecure` for the isolated data directory, then loopback :53306 with mysqlx/local-infile disabled and secure-file-priv=NULL; seed `infra/mysql.sql`; root password set to the public test-only value. Application uses SELECT-only workbench_reader.
- SQLite `samples/sample.sqlite`: actual connection with mode=ro/query_only/authorizer; direct DELETE, ATTACH and load_extension denied. Limit overrun explicitly fails.

Test instances can be stopped with `scripts/portable_databases.ps1 -Stop`. Do not redistribute ignored downloaded binaries or use these fixture passwords outside this test setup.

## Screenshots and review

- [Landing/import workspace](evidence/01-workbench.png)
- [Analysis and controls](evidence/02-analysis.png)
- [Version history](evidence/03-history.png)
- [Recorded-demo chart viewport](evidence/05-chart-viewport.png)
- [Final full workspace](evidence/04-final-workbench.png), [English UI](evidence/06-english-workbench.png), [recorded demo](evidence/demo.webm)
- [Chinese dark Plotly chart](evidence/themes/plotly/dark/chart.png)
- [Report Matplotlib chart](evidence/themes/matplotlib/report/chart.png)
- [Dark Altair exact-size chart](evidence/themes/altair/dark/chart.png)
- [ECharts legend spacing](evidence/themes/echarts/dark/chart.png)
- [Geo points](evidence/gallery/geo/chart.png), [density](evidence/gallery/density/chart.png), [table](evidence/gallery/plottable/chart.png)
- [Long labels and percent units](evidence/long-labels/echarts/chart.png)

Earlier failed runs are retained under `evidence/earlier-failures`: a Plotly batch-export size regression (700×500 instead of 1000×560) was fixed by explicit export dimensions; a concurrent Chromium capture failed once and the subsequent E2E rerun passed. Earlier date-inference, database dialect and font failures were fixed rather than deleting their scenarios. Live model repetitions are absent, not fabricated.

## Unexecuted / remaining

Clean Docker build, actual container worker network/resource checks and all three live model paths remain unverified. No public release is claimed. CI is supplied but its remote execution is not claimed. Next action is specified in [STATUS](STATUS.md).
