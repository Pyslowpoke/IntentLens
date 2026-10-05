# Public interactive sample / 公开互动体验

**[Open the sample / 打开体验](https://pyslowpoke.github.io/IntentLens/)** · [English](https://pyslowpoke.github.io/IntentLens/?lang=en)

This standalone sample is hosted on GitHub Pages from `demo/`. It demonstrates metric confirmation, real aggregation, chart refinement and download. It does **not** call a model or expose the full workbench API.

## Scope

- Twelve explicitly synthetic records: four regions × three months.
- Sales totals, overall conversion and simple mean monthly conversion.
- Title, color, ascending/descending ordering and undo for applied style changes.
- Actual SVG, computed CSV and JSON downloads. JSON includes the source records, definitions and results.
- Chinese/English and responsive mobile layout. No account, upload, API key or backend.

The full application adds Excel/CSV imports, server-side model discussion, multiple chart engines, persistent projects and revisions. The sample does not claim to test those features or represent the full application's latency. It deliberately offers fixed questions rather than pretending to understand arbitrary natural-language input.

## Verification

```sh
python scripts/verify_demo.py
# Also record four browser screenshots and a 30-second GIF:
python scripts/verify_demo.py --capture docs/evidence
```

Requires the repository's development dependencies and Playwright Chromium. The script serves the page on an ephemeral loopback port, checks known sales and ratio values, downloads actual files, recalculates the JSON bundle, verifies undo and escaped title input, checks English/mobile presentation, and rejects runtime requests to external services. It does not require the API, worker or a model key.

Local manual preview:

```sh
python -m http.server 8766 --bind 127.0.0.1 --directory demo
```

Open `http://127.0.0.1:8766`. Clicking the repository links navigates to GitHub; normal calculation does not send requests outside the page's origin. GitHub Pages serves the site and may process ordinary hosting requests; this is not a claim of anonymous hosting.

## Publishing

`.github/workflows/demo-pages.yml` uploads only `demo/`, never the repository root, local `.env`, data directories or API processes. GitHub Pages uses the Actions publishing source. Pushes to `main` affecting the demo trigger deployment; other changes can be published through workflow dispatch.

The README walkthrough is recorded from this rules-only sample, not from a live model call. Four seven/eight-second scenes show the plan, chart, style edit and successful SVG download, for a 30-second loop.

## Suggested launch text / 发布文案草稿

中文：

> 我做了一个可本地运行的数据可视化工作台 IntentLens。先确认分组、聚合和比例口径，再用真实数据计算图表；可以连续改图、回溯版本和导出。现在提供不用安装的合成数据互动体验，明确使用规则模式，不调用 AI。欢迎试试总体转化率与简单平均的区别，也欢迎反馈安装和使用中卡住的地方。

English:

> IntentLens is a local data-visualization workbench with explicit metric definitions, computed results, chart revisions and reproducible exports. Try the no-install synthetic sample to compare overall conversion with a simple mean, refine a chart and download it. The public sample uses rules, not AI; the full workbench supports configured model conversations and your own spreadsheets. Feedback on the first-run experience is welcome.

These drafts have not been posted to any community or sent to other people.
