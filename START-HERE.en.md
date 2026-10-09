# First run

IntentLens runs three local services: web, API and worker. Use rule mode first; it requires no model key.

## Windows

Install Node.js 24 and Python 3.12, then pnpm 11.25.0 and uv 0.12.19. Download the repository and run the root `首次安装.cmd` (first install). For later launches use `启动观意.cmd`. Open http://127.0.0.1:3000 after the web server reports Ready. Keep the launcher open while using the app. First install needs network access.

## Manual setup

Copy `.env.example` to `.env`; keep secrets server-side. From the repository root run `uv sync --frozen`, run `pnpm install --frozen-lockfile` and `pnpm --dir apps/web prepare-assets`, then `pnpm --dir apps/web build`. Start `uv run uvicorn services.api.main:app --host 127.0.0.1 --port 8000`, `uv run python -m services.worker.main`, and `pnpm start` (in apps/web) in separate terminals. Install rendering Chromium with `uv run playwright install chromium`.

## One task to try

Load the synthetic sales sample; generate a rule proposal, execute it, change its title, download a chart, then refresh. Rule mode does not understand arbitrary natural language. Configure a compatible remote model to test conversational analysis; inspect privacy disclosures first.

If a chart fails to appear, report the last displayed step, version, mode and sanitized error. Never publish `.env`, customer data or full private logs. See docs/USER-TRIAL.md.
