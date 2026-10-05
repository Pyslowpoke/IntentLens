# 观意 IntentLens

**Turn Excel/CSV into traceable charts: confirm the metric, compute from data, refine and export.**

[Try the interactive sample](https://pyslowpoke.github.io/IntentLens/?lang=en) · [Install the full workbench](START-HERE.md) · [中文](README.zh-CN.md)

![30-second interactive sample walkthrough](docs/evidence/intentlens-demo.gif)

- **Inspect the definition:** explicit grouping, aggregation, ratio and missing-value rules.
- **Keep a traceable result:** real calculations, chart revisions and reproduction packages.
- **Refine and download:** edit a chart and export without losing the preview on export failure.

The public sample runs locally in your browser on synthetic data, with rules rather than AI. It requires no installation, account or API key. The full workbench supports your own files and configured model conversations. [Demo scope and verification](docs/PUBLIC-DEMO.md).

> New here? Read [START-HERE.md](START-HERE.md) for first-run setup and configuration. Windows launchers are provided in the repository root.

A local, single-user analysis studio: import business data, choose a validated plan, run real calculations, revise a chart, and reopen its complete history. **Intent-driven analysis, grounded in evidence.** See the [product concept](docs/BRAND.md). **This is a development delivery, not a fully accepted V1 release**; see [verification](docs/VERIFICATION.md) and [status](docs/STATUS.md).

[中文说明](README.zh-CN.md) · [Architecture decisions](docs/DECISIONS.md) · [Security boundaries](docs/SECURITY.md) · [Synthetic samples](samples/DICTIONARY.md)

![Workbench](docs/evidence/intentlens-cover.png)

## Quick start

See [GitHub preparation and environment configuration](docs/GITHUB.md) for pip installation, `.env`, dependency exports, and publishing. `requirements.txt` contains runtime dependencies; `requirements-dev.txt` also includes test dependencies. Both are exported from `uv.lock`.

Requirements: Node.js 24, pnpm 11.25.0, Python 3.12, uv. Run commands from this repository.

```sh
cp .env.example .env  # PowerShell: Copy-Item .env.example .env
uv sync --frozen
pnpm install --frozen-lockfile
pnpm --dir apps/web prepare-assets
uv run playwright install chromium
uv run python scripts/generate_samples.py
```

Start three terminals:

```sh
uv run uvicorn services.api.main:app --host 127.0.0.1 --port 8000
uv run python -m services.worker.main
pnpm dev
```

Open **http://127.0.0.1:3000**. Health: http://127.0.0.1:8000/health. API schema: http://127.0.0.1:8000/docs.

On Windows, `powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Install` prepares and starts the three services (API/worker hidden; web in the terminal). Without `-Install`, it uses installed dependencies. Normal Ctrl+C exit cleans up the API and worker started by this launcher. Only one worker may run against a data directory.

## Docker Compose

```sh
pnpm install --frozen-lockfile
pnpm --dir apps/web prepare-assets
docker compose up --build
```

The worker has no network, model keys, database credentials or Docker socket; its filesystem is read-only except the shared data volume and temporary directory, with CPU/memory/process limits. API and web bind host loopback. The Docker clean-build path has **not yet been executed on the current Windows host, where Docker is unavailable**. Do not equate a supplied Compose file with verified deployment.

## Workflow

Open **Settings** in the top-right corner to choose Chinese or English, a nickname, a preferred visualization tool, and a default chart theme. Preferences persist in this browser. New analyses use these defaults; incompatible tools fall back to automatic matching with a notice. Existing charts and user-authored data remain unchanged. Model requests include the selected language; regenerate saved advice to request another language.

1. Import `.xlsx`, `.csv`, `.tsv`, paste a tab-separated table, or use one of three clearly synthetic samples. Preview sheets/header rows/encoding/delimiters before import.
2. Describe a business question. Rule mode produces 2–3 explicit descriptive plans without claiming an AI call. Configured model mode proposes 2–4 plans using server-side adapters. Review assumptions and missing denominators.
3. Run a plan. Every number is calculated from the immutable Parquet snapshot. Advanced JSON exposes stable field IDs, grouping, filters, missing-value policy, time grain, sums/means/counts and both ratio definitions.
4. Refine the current chart with `title: Regional sales`, `blue`, `descending`, `filter Region=East`, `undo`, or Chinese equivalents. Bound chart/revision IDs prevent cross-chart edits. Model mode can translate additional instructions; all resulting plans are validated. Advanced JSON supports the full declarative contract.
5. Switch compatible engines, themes and dimensions. Interactive engines deliver the HTML preview first; static engines deliver PNG first. Other supported files are generated on download, and export failures preserve the chart. Default reproduction ZIP contains the snapshot checksum/reference, plan, chart configuration, controlled code and dependency lock, **not data rows**. The explicitly labeled second download includes the snapshot.
6. Projects, questions, runs and revisions persist in SQLite. Undo/restore create a new revision, preserving ancestry. Restarting a worker marks interrupted runs failed and offers retry. New datasets or requests supersede stale work.

## Delivery reliability and live verification

Chart publication does not wait for every export format. Plotly/Altair/ECharts publish HTML first; image/PDF export runs on demand in a separate process with a 45-second timeout. Download errors leave the preview and revision available. Queued jobs expire after `RUN_QUEUE_TIMEOUT` (default 60 seconds); abandoned running jobs expire after `RUN_TIMEOUT` + 30 seconds. Execution/publication exceptions become failed runs with retry feedback.

The model protocol uses stable field IDs and the computed `value` column for aggregated metrics, with validation before execution. Live DeepSeek checks on synthetic data covered sales aggregation, conversion ratios and follow-up discussion. One browser run measured recommendation **4.522 s**, follow-up **4.249 s**, and execution to a visible chart **5.680 s**, with a successful PNG download. These are individual observations, not latency guarantees or P95 estimates. See [live verification and reproduction](docs/LIVE-VALIDATION.md).

## Capability matrix

| Engine | Implemented scope | Export |
|---|---|---|
| Plotly | line, bar, scatter, area, histogram, box, heatmap | PNG, SVG, PDF, interactive HTML |
| Matplotlib / Seaborn | line, bar, scatter, histogram, box, violin, heatmap | PNG, SVG, PDF |
| Altair / Vega-Lite | line, bar, scatter, area, facet, brush-linked view | PNG, SVG, PDF, HTML |
| pyecharts / ECharts | basic line/bar/scatter, sankey, tree, funnel | PNG via Chromium, offline HTML |
| Datashader | full-data scatter density and explicit viewport recomputation | PNG; counts per pixel, no per-point hover |
| GeoPandas + pydeck | WGS84 longitude/latitude, categorical encoding, tooltips, no basemap | offline HTML, static GeoPandas PNG |
| plottable | formatted ranking/KPI table, up to 40 rows | PNG, SVG, PDF |

SVG/PDF are vector for ordinary 2D charts; Plotly WebGL traces can embed raster content. The registry reports engine limits. Large ordinary chart results are rejected above 20,000 marks; choose aggregation/density. No silent sampling or truncation. Dark, light and report theme adapters exist; cross-engine visual parity is not claimed.

## Database sources

Configure on the API process only. `.env.example` documents variables; native API/worker commands load allowed variables from root `.env` at startup; process environment variables take priority. SQLite values are explicitly chosen absolute database files; browser input cannot choose an arbitrary host path.

```text
SQLITE_FILES_JSON={"sample":"/absolute/path/to/samples/sample.sqlite"}
DB_SOURCES_JSON={"warehouse":"postgresql+psycopg://reader:password@localhost:5432/db","mysql":"mysql+pymysql://reader:password@localhost:3306/db"}
```

Use truly restricted SELECT-only accounts. Connectors validate account restrictions, establish read-only connections/transactions, apply a five-second query timeout and reject more than 10,000 returned rows. Queries are parsed, but AST validation is only an additional boundary. Browse, preview and snapshot results through the database dialog/API. SQL drafts are always returned for review, never auto-executed.

Synthetic integration services:

```sh
docker compose -f infra/databases.compose.yaml up -d --wait
uv run pytest -m database
docker compose -f infra/databases.compose.yaml down
```

The current delivery also actually tested official portable PostgreSQL 17.11 and MySQL 8.4.11 on loopback ports 55432/53306; binaries are ignored in `.local/` and are not distribution artifacts. Fixture passwords are public test-only values.

## Models and privacy

Default: `PROVIDER=rule`, no key required. API process variables: `PROVIDER=deepseek|openai|anthropic|ollama`, `MODEL`, optional `MODEL_BASE_URL`, and `MODEL_API_KEY` for remote authenticated providers. DeepSeek defaults to `deepseek-flash`; other providers require a model name. OpenAI-compatible uses `/chat/completions`; Anthropic uses its own `/messages` and headers; Ollama uses `/api/chat` with native JSON schema and `stream:false`.

Only field metadata and numeric/date statistics are sent by default, not raw row samples. Metadata can be sensitive. Local hosting does not make remote inference local. Credentials never belong in frontend variables, exports or source control. Protocol/error tests use mocks to test wire shapes; opt-in live DeepSeek tests were also run with configured credentials on synthetic data. No cost estimate is invented. Arbitrary generated Python and JavaScript are disabled.

## Validation and benchmarks

Pre-push check (2026-10-05): **70 non-database Python tests and 9 frontend tests passed**; TypeScript typecheck passed. The opt-in real-model browser flow passed on 2026-10-04; see [live validation](docs/LIVE-VALIDATION.md).

```sh
uv run pytest -m 'not database'
uv run pytest -m database
pnpm typecheck
pnpm build
pnpm test
pnpm e2e  # all three services running
uv run python -m scripts.benchmark
uv run python -m scripts.render_gallery
```

Known-answer tests cover ratio semantics, missing fields, dates, encoding, duplicated headers, actual database write denial, actual worker timeouts/cancellation/stale completion, persistent revisions and provider errors. Browser E2E covers the real UI and five edits. [Evidence](docs/evidence/) includes screenshots, JUnit, rendered outputs and measured benchmark JSON. Benchmarks aggregate all rows into 20 groups; they are not a claim to render one million SVG markers or to outperform other products.

## Repository and limitations

`apps/web` Next.js UI; `services/api` contracts, connectors and validated operations; `services/worker` isolated execution loop; `packages/contracts` exported schemas; `samples` synthetic data; `tests` known-answer and integration tests; `infra` deployment and database fixtures.

See [STATUS](docs/STATUS.md) for unfinished mandatory acceptance. Native mode does not enforce OS network isolation or a total process memory limit. This development server is not for public untrusted users. No cloud resources were provisioned and nothing was published. The release does not yet include arbitrary multi-table relationship inference, authentication, multi-tenancy or streaming.

## Contributing and license

Read [CONTRIBUTING](CONTRIBUTING.md). A permissive **Apache-2.0** repository license is suggested, subject to the owner's decision; no project LICENSE has been imposed. Dependency license inventories and obligations are in [THIRD_PARTY](docs/THIRD_PARTY.md). Retain original dependency notices, including LGPL psycopg and MPL certifi obligations, when distributing. Official database binaries and Windows fonts are not redistributed by this project.
