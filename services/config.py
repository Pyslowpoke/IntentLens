"""Load repository .env at service startup; process environment takes priority."""
import os
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
COMMON = {"WORKBENCH_DATA", "RUN_TIMEOUT", "RUN_MAX_MB"}
API = COMMON | {"MAX_UPLOAD_MB", "MAX_ROWS", "PROVIDER", "MODEL", "MODEL_BASE_URL", "MODEL_API_KEY", "DB_SOURCES_JSON", "SQLITE_FILES_JSON"}


def load_environment(service: str, path: Path | None = None):
    allowed = API if service == "api" else COMMON
    for name, value in dotenv_values(path or ROOT / ".env", encoding="utf-8-sig", interpolate=False).items():
        if name in allowed and value is not None:
            os.environ.setdefault(name, value)
