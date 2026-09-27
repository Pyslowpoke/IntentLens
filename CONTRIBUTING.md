# Contributing

1. Read docs/STATUS.md and docs/DECISIONS.md before changing architecture.
2. Use Python 3.12 and Node 24. Keep uv.lock and pnpm-lock.yaml committed. Do not commit .env, data/, .local/, keys or credentials.
3. Change Pydantic contracts first and regenerate `python -m scripts.export_contracts`. Unknown fields and unsafe operations should fail explicitly.
4. Keep calculation separate from rendering. Add independent known-answer assertions for numerical changes. Do not compute expected values by calling the same production function.
5. Run core Python tests, typecheck/build, component tests and relevant E2E. Database changes require actual database services, not mocks. Renderer changes require opening generated images and checking Chinese text, negative signs, legends, margins and dimensions.
6. Update STATUS and VERIFICATION with actual commands and evidence. Do not label unexecuted CI, a declared feature, or skipped tests as verified.

The repository license is pending owner selection. Do not publish packages, deploy a public site or issue announcements without authorization.
