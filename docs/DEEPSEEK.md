# DeepSeek 接入与决策支持

推荐复制根目录 `.env.example` 为 `.env`，设置 `PROVIDER=deepseek`、`MODEL=deepseek-flash`、`MODEL_BASE_URL=https://api.deepseek.com` 和自己的 `MODEL_API_KEY`，然后重启 API。系统环境变量优先于 `.env`。

也可使用 Windows 兼容配置方式，在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\configure-deepseek.ps1
```

按提示隐藏输入自己的 DeepSeek API Key。脚本保存到被 Git 忽略的 `.local/model.json`，并限制 Windows 文件访问权限。文件包含明文密钥，请勿分享；密钥不会发送给浏览器或加入复现包。默认服务为 `https://api.deepseek.com`，模型为当前官方 JSON 示例中的 `deepseek-flash`。可通过脚本的 `-Model` 参数指定账户支持的模型。

API 每次请求重新读取本地配置，保存后刷新页面即可。已有环境变量和根目录 `.env` 中的 `PROVIDER/MODEL/MODEL_BASE_URL/MODEL_API_KEY` 优先；如之前设置了 `PROVIDER=rule`，需要清除覆盖并重启 API。容器使用这四项环境变量，不能读取宿主机本地配置。

使用流程：导入数据 → 输入业务问题 → 模型模式生成方案 → 选择并执行方案 → 图表下方“生成决策建议”。规则模式生成的聚合图表也可请求模型决策支持。

决策包含摘要、行动、证据编号、风险、下一步、局限与待补充问题。输入为当前分析计划及最多前 100 组实际聚合结果；禁止原始明细模式，显示截取范围。程序验证输出结构和证据编号，但不能保证模型的解释或业务判断正确。建议不会自动执行外部业务操作。结果按不可变图表版本保存，图表变化后显示对应版本的建议。

接口：`GET /model/status`（仅返回提供商、模型、配置是否齐备），`POST /projects/{id}/decision`（传入 revision_id 和 goal），`GET /projects/{id}/decision`（读取当前版本建议）。ready 仅表示配置齐备，不代表密钥已通过真实鉴权。

验证：30 项 Python 测试通过，涵盖 DeepSeek 请求协议、鉴权错误脱敏、无效输出、证据数量限制、生成期间版本变化、存储读取；前端类型检查、生产构建、3 项单元测试通过；浏览器端到端测试通过（23.2 秒），包含决策入口与缺失密钥提示。真实 DeepSeek 请求需要用户配置密钥，尚未验证。

官方协议参考：https://api-docs.deepseek.com/guides/json_mode/
