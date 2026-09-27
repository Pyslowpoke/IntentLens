# GitHub 发布准备与安装

## 依赖约定

- Python 3.12：`pyproject.toml` 声明直接依赖，`uv.lock` 是依赖版本来源。
- `requirements.txt` 是运行依赖，`requirements-dev.txt` 包含运行和测试依赖；二者从锁文件导出，包含哈希，不要手工编辑。
- Node.js 24、pnpm 11.25.0：使用 `package.json` 与 `pnpm-lock.yaml`；`.nvmrc`、`.python-version` 声明版本。

推荐按 README 使用 `uv sync --frozen`。不使用 uv 时，在根目录执行：

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --require-hashes -r requirements-dev.txt
python -m playwright install chromium
pnpm install --frozen-lockfile
pnpm --dir apps/web prepare-assets
python scripts/generate_samples.py
```

只运行应用可将 requirements-dev.txt 替换为 requirements.txt。Linux 无桌面环境时使用 `python -m playwright install --with-deps chromium` 并安装中文字体。分别在三个终端启动：

```sh
python -m uvicorn services.api.main:app --host 127.0.0.1 --port 8000
python -m services.worker.main
pnpm dev
```

## 环境变量

复制 `.env.example` 为根目录 `.env`，默认规则模式无密钥也能运行。DeepSeek 设置：

```dotenv
PROVIDER=deepseek
MODEL=deepseek-flash
MODEL_BASE_URL=https://api.deepseek.com
MODEL_API_KEY=替换为自己的密钥
```

API 在启动时读取 `.env`；Worker 只加载数据目录和任务资源限制，不从文件加载模型或数据库密钥。系统环境变量优先，修改后重启相关服务。前端不读取模型密钥，不使用 NEXT_PUBLIC_ 前缀存储密钥。兼容的 `.local/model.json` 优先级最低。

GitHub Actions 的基础测试不需要真实模型密钥。部署时在目标主机配置 `.env` 或容器环境变量，不把个人 `.env` 放进仓库。Compose 会读取根目录 `.env` 并将选定变量传给 API。

## 更新依赖

```sh
uv lock
uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt
uv export --frozen --no-emit-project --format requirements-txt --output-file requirements-dev.txt
```

同时提交 pyproject.toml、uv.lock 和两个 requirements 文件。前端依赖修改后同时提交 package.json 与 pnpm-lock.yaml。CI 检查 requirements 导出是否同步。

## 提交到 GitHub

提交源代码、配置模板、依赖锁文件、测试、文档及合成样例。`.gitignore` 排除 `.env` 及其本地变体、`.local/`、`data/`、依赖目录、日志、测试缓存与构建产物；Docker 构建上下文也排除本地配置。

尚未替项目选择开源许可证；发布公开仓库不等于授予开源使用许可，许可证由项目所有者决定。

当前目录未初始化 Git，也未关联远程仓库。准备好自己的 GitHub 空仓库后运行以下命令（替换远程地址）：

```sh
git init -b main
git add .
git diff --cached --stat
git diff --cached
git commit -m "Initial workbench implementation"
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

提交前检查暂存内容，不应包含真实业务数据或密钥。Docker 启动和真实模型调用仍需在具备对应运行环境及凭据时验证。

## 本次整理验证

- 环境配置、模型适配、决策接口及核心逻辑：32 项测试通过。
- `uv lock --check` 与 `uv pip check` 通过。
- 使用隔离 Git 元数据检查：`.env`、`.env.production`、本地模型配置、运行数据、node_modules、Next 构建目录均被忽略；`.env.example` 与 requirements 保留。
- 280 个候选文件中没有超过 95 MiB 的单文件。尚未初始化项目 Git 仓库或推送远程，也未在 GitHub 托管运行器上执行 CI。
