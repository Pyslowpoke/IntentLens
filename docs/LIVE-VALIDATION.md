# Delivery and live-model verification / 交付与真实模型验证

Measured on 2026-10-04 (Asia/Shanghai); documentation updated 2026-10-05.

## What changed

- Preview publication is independent of optional static export. Export exceptions/timeouts retain the chart.
- Failed worker execution or result publication terminates the run. Polling expires abandoned queued/running jobs instead of waiting forever.
- Structured model instructions require stable field IDs, computed `value` mapping and accurate missing/unique-count interpretation; unknown fields remain rejected.

## Observed live results

Provider: configured DeepSeek (`deepseek-v4-flash`). Only synthetic datasets were used. Fixed known answers: sales East=400, West=200; overall conversion East=500/3000, West=150/1500. A vague question followed by an explicit grouping/metric request also produced an executable plan.

After the prompt correction, those three cases produced charts: recommendation 4.33–4.59 seconds; worker execution 2.28–2.31 seconds. A separate browser run with the 720-row synthetic sales sample measured recommendation 4.522 seconds, follow-up 4.249 seconds, execution until visible Plotly bars 5.680 seconds, and successful PNG download. Worker timing is not browser end-to-end timing.

Initial live attempts included a derived-label mapping rejected by field validation and an invalid structured response. The first browser harness attempt used an incorrect selector; after correcting it, the complete flow passed. These failures are not omitted from the interpretation: successful fixed cases do not establish universal model reliability or latency guarantees.

## Publication checks

Pre-push regression on 2026-10-05: **70 Python tests passed**, 2 database tests deselected; TypeScript typecheck passed and **9 frontend tests passed**. Live-model browser validation was performed on 2026-10-04; it was not repeated for publication.

## Reproduce

Start API, one worker and web as described in the README. Use a separate `WORKBENCH_DATA` directory for tests to keep test projects separate from personal analyses. Configure model credentials only in ignored `.env` or server environment variables. Ordinary regression tests do not require paid model calls.

```sh
uv run pytest tests/test_delivery.py tests/test_core.py tests/test_providers.py tests/test_user_journeys.py
pnpm typecheck
pnpm test
pnpm --dir apps/web exec playwright test e2e/delivery.spec.ts
```

Real-model browser test is opt-in and consumes API credits. In PowerShell, with the three services running against the test data directory and a configured model:

```powershell
$env:ALLOW_LIVE_MODEL_TEST = '1'
pnpm --dir apps/web exec playwright test e2e/live-model.spec.ts
Remove-Item Env:ALLOW_LIVE_MODEL_TEST
```

Playwright writes screenshots and timings to its test output. The test verifies visible chart marks and PNG download, rather than merely waiting for an execution status.

## Limits / 边界

These are small fixed-case observations, not P95 measurements or a production stability benchmark. Docker, multi-user load and every engine/workbook combination were not newly validated. Native execution remains intended for a trusted local user. A missing static-export browser can still prevent image downloads; the preview remains available.
