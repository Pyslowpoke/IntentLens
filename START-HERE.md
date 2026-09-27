# 第一次使用，从这里开始

这是在自己电脑上运行的网页应用，不是直接打开 Python 或 TSX 文件的单文件程序。网页、后台接口、后台计算服务需要一起启动。

## Windows 首次使用

1. 安装 **Node.js 24**（https://nodejs.org/）和 **Python 3.12**（https://www.python.org/downloads/）。安装 Python 时勾选 **Add python.exe to PATH**。
2. 重新打开 PowerShell，执行下面两行，安装项目所需的依赖管理工具：

```powershell
npm install -g pnpm@11.25.0
python -m pip install uv==0.12.19
```

关闭并重新打开终端，运行 `node --version`、`pnpm --version`、`uv --version`，都应显示版本；若提示找不到命令，先修复安装或 PATH。

3. 下载 GitHub ZIP 并解压，进入包含本文件的文件夹，双击 **首次安装.cmd**。它会创建 `.env`、安装依赖与绘图浏览器，并启动程序。首次下载需要联网，失败时查看保留的终端报错。
4. 等终端显示 **Ready**，在浏览器打开 **http://127.0.0.1:3000**。

不填 API 也能先使用合成数据体验规则分析。以后双击 **启动观意.cmd** 即可，无需反复安装。使用期间保留终端窗口，正常停止请按 **Ctrl+C**，脚本会结束本次启动的后台服务。不要同时启动多份。

## 我在哪里填 API？

双击 **编辑配置.cmd**，会用记事本打开根目录 `.env`，没有则自动创建。

- `.env.example`：随代码分发的空白配置模板。
- `.env`：你本机实际使用的配置，与 README 在同一个文件夹。
- `.env` 可能含密钥，所以不会上传 GitHub；每位下载者由启动脚本创建自己的文件。

接入 OpenAI 格式的服务，只修改这四行，将示例文字换成真实值：

```dotenv
PROVIDER=openai
MODEL=服务商给你的模型名称
MODEL_BASE_URL=https://服务商的基础地址/v1
MODEL_API_KEY=你的密钥
```

`PROVIDER` 是接口类型，`MODEL` 是模型 ID，`MODEL_BASE_URL` 是服务商给的 Base URL，`MODEL_API_KEY` 是访问密钥。不要给地址追加 `/chat/completions`。DeepSeek 官方使用 `PROVIDER=deepseek`、`MODEL_BASE_URL=https://api.deepseek.com`，模型填账户支持的型号。

暂时不用 AI 时保持 `PROVIDER=rule`，另外三项留空。文件后半部分的大小、内存、数据库等高级配置都不用改。保存后停止并重启程序才会生效。不要保存成 `.env.txt`。系统环境变量优先于文件配置。

## 代码真正从哪里运行？

| 内容 | 位置 | 作用 |
|---|---|---|
| Windows 总入口 | `启动观意.cmd` → `scripts/start.ps1` | 一起启动下面三部分 |
| 网页主界面 | `apps/web/app/page.tsx` | `pnpm dev` 运行，端口 3000 |
| 后端接口 | `services/api/main.py` | uvicorn 运行，端口 8000 |
| 后台计算 | `services/worker/main.py` | 执行计算和绘图任务 |
| 外部模型调用 | `services/api/providers.py` | 读取模型配置并请求服务商 |
| 实际配置文件 | `.env` | 模板是 `.env.example` |

需要分别调试时，在项目根目录打开三个终端，分别执行：

```powershell
.\.venv\Scripts\python.exe -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m services.worker.main
pnpm dev
```

上面是三个独立进程，不是在一个终端里等三行依次执行。使用总启动入口时不用手动执行它们。

## 常见问题

- 找不到 `.env`：双击编辑配置.cmd，自动创建并打开。
- 网页打不开：检查启动窗口是否显示 Ready，不要直接打开 page.tsx。
- 端口已占用：先检查应用是否已经运行；修改配置后需停止旧服务再启动。
- 模型调用失败：检查四项配置、密钥、账户余额和接口兼容性。配置齐备不代表鉴权成功。
- 生成任务一直等待：检查根目录 worker-error.log；API 错误查看 api-error.log。
- 安装失败：按终端错误检查网络或依赖，解决后重新运行首次安装.cmd。

macOS/Linux 请使用 README 的 uv/pnpm 三终端方式。当前不是免安装桌面软件，下载后仍需准备运行工具和依赖。Windows 启动脚本不能在其他系统直接运行。
