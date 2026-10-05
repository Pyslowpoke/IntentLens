# 观意 IntentLens

> **第一次下载？先看 [第一次使用指南](START-HERE.md)。** Windows：安装运行工具后双击 `首次安装.cmd`；以后双击 `启动观意.cmd`；配置 API 双击 `编辑配置.cmd`。

面向产品、运营与分析人员的本地单用户工作台：输入数据、描述问题、选择分析方案、执行真实计算、连续改图、导出并恢复历史。**先理解问题，再看见答案。** 品牌理念见 [观意的产品概念](docs/BRAND.md)。**当前交付是可运行的开发版本，尚不能称为全部验收通过的 V1。** 事实与缺项见 [验证报告](docs/VERIFICATION.md) 和 [阶段状态](docs/STATUS.md)。

## 启动

准备上传 GitHub、使用 pip 安装或配置 `.env`，请查看 [仓库发布与配置指南](docs/GITHUB.md)。Python 依赖提供 `requirements.txt`（运行）和 `requirements-dev.txt`（含测试），均由 `uv.lock` 导出。

DeepSeek 模型配置与决策建议使用方法见 [DeepSeek 接入说明](docs/DEEPSEEK.md)。推荐在根目录 `.env` 设置模型和密钥后重启 API；Windows 隐藏输入脚本是兼容方式，优先级低于 `.env`。

需要 Node.js 24、pnpm 11.25.0、Python 3.12、uv。在仓库根目录运行：

```sh
cp .env.example .env  # PowerShell: Copy-Item .env.example .env
uv sync --frozen
pnpm install --frozen-lockfile
pnpm --dir apps/web prepare-assets
uv run playwright install chromium
uv run python scripts/generate_samples.py
```

分别在三个终端启动：

```sh
uv run uvicorn services.api.main:app --host 127.0.0.1 --port 8000
uv run python -m services.worker.main
pnpm dev
```

打开 **http://127.0.0.1:3000**。API 文档位于 **http://127.0.0.1:8000/docs**。

Windows 可执行 `powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Install`，自动准备依赖并启动 API、worker 和前端。再次运行不需要 `-Install`。正常按 Ctrl+C 退出时，脚本会清理本次启动的 API/worker。同一数据目录只运行一个 worker。

Docker 启动：先准备 ECharts 静态资源，然后 `docker compose up --build`。Compose 配置包含无网络 worker、只读文件系统、CPU/内存/进程限制，不挂载 Docker socket。**当前主机缺少 Docker，因此尚未完成干净容器构建与运行验收。**

## 使用

右上角“设置”支持简体中文 / English、昵称、默认可视化工具与图表主题。偏好保存在当前浏览器，刷新后恢复，也可恢复默认值。新分析应用所选工具；图表类型不兼容时提示并自动匹配。已有图表不受影响，用户数据、项目名称及历史分析不会自动翻译。模型请求带上所选语言，已保存的建议保留原文，可重新生成。

1. 上传 Excel/CSV/TSV，先选择工作表、表头行、编码和分隔符并预览，再导入。也可粘贴 Tab 分隔表格或选择销售订单、产品使用、医院拓展三组合成数据。
2. 输入业务问题，选择规则模式或已配置的服务端模型。规则模式不调用 AI，推荐结果明确标注假设；缺少目标总体时不会编造渗透率。
3. 选择方案执行。界面“数据明细”可查看字段空值/唯一值并修正类型；高级配置使用 `f1`、`f2` 等稳定字段 ID，可修改分组、聚合、筛选、缺失值策略、时间粒度与比例口径。
4. 连续修改支持“标题：区域销售表现”“改成蓝色”“按数值降序”“筛选 地区=华东”“撤销”，以及明确字号、标注、尺寸与图型指令。模型模式可理解更多指令，结果仍经过契约校验。操作绑定当前图表与版本，不靠对话猜测对象。
5. 兼容引擎可以切换；不兼容会明确拒绝。样式修改复用计算结果，筛选改变会重算。历史恢复生成新分支，不破坏旧版本。Plotly/Altair/ECharts 先交付交互图，静态引擎先交付 PNG；其他导出文件点击下载后生成，导出失败不影响已生成的图表。排队超过60秒或执行器超出期限仍未返回时，明确标记失败并允许重试。
6. PNG/SVG/PDF/HTML 按实际产物展示按钮。默认可复现包只含快照校验值、计划、配置、受控代码和锁文件，不含原始数据；第二个下载入口明确包含数据快照。

## 结果交付与真实模型验证

图表发布不再等待全部导出格式。Plotly/Altair/ECharts 先生成 HTML；图片和 PDF 在点击下载后由独立进程生成，45 秒超时，失败时保留预览与版本。`RUN_QUEUE_TIMEOUT` 默认 60 秒，失联的运行中任务在 `RUN_TIMEOUT` + 30 秒后终止等待；执行和保存异常会标记失败并提供重试反馈。

模型协议明确稳定字段 ID，以及聚合/比例结果的数值列 `value`，执行前仍严格校验字段。真实 DeepSeek 合成数据测试覆盖销售额汇总、总体转化率和多轮追问。一轮浏览器实测：推荐 **4.522 秒**、追问 **4.249 秒**、执行到图形可见 **5.680 秒**，PNG 下载成功。以上是单次观察，不是耗时保证或 P95；详见[真实调用记录与复现](docs/LIVE-VALIDATION.md)。

## 能力矩阵

| 引擎 | 范围 | 导出 |
|---|---|---|
| Plotly | 折线、柱、散点、面积、直方、箱线、热力图 | PNG/SVG/PDF/HTML |
| Matplotlib / Seaborn | 基础图、分布、箱线、小提琴、热力图 | PNG/SVG/PDF |
| Altair / Vega-Lite | 基础图、分面、刷选联动视图 | PNG/SVG/PDF/HTML |
| pyecharts / ECharts | 基础图、桑基、树、漏斗 | PNG/离线 HTML |
| Datashader | 全样本散点密度、手动视口范围重算 | PNG，每像素计数，无逐点 hover |
| GeoPandas + pydeck | WGS84 点位、分类、提示、无底图 | 离线 HTML/静态 PNG |
| plottable | 带格式的排名/KPI 表格，最多 40 行 | PNG/SVG/PDF |

一般二维图的 SVG/PDF 为矢量；Plotly WebGL 可能含位图。引擎限制显示在设置栏。普通图超 2 万个标记会拒绝，要求用户先聚合或使用密度图，不能截取前 N 行充当完整分析。主题实现了浅色、深色和报告，但不宣称跨引擎像素一致。

## 计算口径

- 总体比例：分子求和÷分母求和；简单平均比例：每行比例的算术平均。分母为零明确报错。
- 缺失值策略必须明确：报错、排除，或保留分组。保留时聚合忽略空指标，不填零；数量是实际行数。
- 按月汇总会显示实际观测日期，并警告边界月份可能不完整，不能把部分月份称为整月下滑。
- 不运行宏；Excel 只读取公式缓存。缺少缓存会指出单元格，要求在 Excel 中计算并保存，不冒充公式引擎。
- 原始文件、转换记录与不可变 Parquet 快照保存在本地 `data/`；超过限制明确拒绝。

## 数据库

只在 API 进程设置 `DB_SOURCES_JSON` 和 `SQLITE_FILES_JSON`，格式参见 `.env.example`。原生 API/worker 启动时读取根目录 `.env` 中允许的配置，进程环境变量优先。浏览器不能随意选择宿主数据库文件或保存密码。

PostgreSQL/MySQL 使用受限只读账号、只读事务、5 秒超时；SQLite 使用明确白名单路径、只读打开和 VM authorizer。最多收集 1 万行，超限要求显式聚合/LIMIT，不静默截断。AST 检查只作补充，不代替数据库权限。

`docker compose -f infra/databases.compose.yaml up -d --wait` 启动测试数据库，然后 `uv run pytest -m database`。本次已在项目内下载并实际运行官方 PostgreSQL 17.11 / MySQL 8.4.11 便携版，在 127.0.0.1 的 55432/53306 端口测试；不注册系统服务。测试凭据仅用于固定合成数据。`.local/` 中二进制不进版本库、不属于分发包。

## 模型、执行与安全

默认 `PROVIDER=rule`，无密钥可完整体验规则闭环。模型由 API 服务端的 `PROVIDER=deepseek|openai|anthropic|ollama`、`MODEL`、`MODEL_BASE_URL`、`MODEL_API_KEY` 配置。三种协议分别实现；没有硬编码模型名。密钥不进入前端、日志、版本或导出包。

默认仅发送字段、空值/唯一值统计、数值/日期范围，不发送原始行；元数据也可能敏感。自部署应用不等于外部模型收不到数据。协议 mock 验证请求和错误处理；另使用已配置的凭据完成了明确启用的 DeepSeek 合成数据实测。少量成功案例不代表模型整体质量，不记录虚构费用。

仅执行受控声明式计划；任意模型 Python/JS 始终关闭。Compose 的 worker 无外网与凭据，并设置资源上限。Windows 原生模式仅用于可信本机开发，不是 OS 沙箱，也不是公共多租户服务。取消、超时和过期任务不会更新项目最新结果；worker 重启把中断任务标为失败并允许重试。

## 验证、演示、贡献

2026-10-05 发布前检查：**70 项非数据库 Python 测试、9 项前端测试通过**，TypeScript 类型检查通过。真实模型浏览器路径已于 2026-10-04 通过，详见[验证记录](docs/LIVE-VALIDATION.md)。

运行 `uv run pytest`、`pnpm typecheck`、`pnpm build`、`pnpm test`。三服务启动后运行 `pnpm e2e`。性能记录由 `uv run python -m scripts.benchmark` 生成，绘图检查由 `uv run python -m scripts.render_gallery` 生成。百万行基准是全量聚合成 20 组，不是百万个 SVG 标记，也不是竞品领先声明。

[演示步骤](docs/DEMO.md)、[验证证据](docs/VERIFICATION.md)、[贡献约定](CONTRIBUTING.md)、[第三方许可](docs/THIRD_PARTY.md)。建议仓库采用 Apache-2.0，但尚未替用户决定许可证或创建 LICENSE。分发前需保留依赖许可，特别是 LGPL psycopg、MPL certifi。未创建云资源、未公开发布、未发送宣传内容。
