# Architecture decisions

- Keep the requested Next.js / FastAPI / independent Python worker architecture.
- Pydantic is the contract authority; generated JSON Schema is checked into packages/contracts.
- Local single-user mode binds loopback. Compose worker has network_mode: none, no secrets, no Docker socket. Native mode is for trusted local use and does not claim OS network isolation.
- Execute an allowlisted declarative plan; arbitrary Python and JavaScript from models remain disabled.
- SQLite CAS updates bind every run to dataset generation and chart head. Revisions are immutable; undo/restore create new child revisions.
- Raw imports are retained privately. Reproduction ZIP defaults to snapshot hash/reference, not raw data; inclusion is explicit.
- Model protocol references: [OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs), [Anthropic](https://platform.claude.com/docs/en/api/messages/create), [Ollama](https://docs.ollama.com/api/chat). Only schemas and profile summaries are sent by default; self-hosting does not prevent external model transfer.
