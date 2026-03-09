import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_cors_origins(raw: str) -> list[str]:
    origins = [item.strip().rstrip("/") for item in raw.split(",")]
    return [origin for origin in origins if origin]


DATABASE_URL: str = _require_env("DATABASE_URL")
SECRET_KEY: str = _require_env("SECRET_KEY")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
CORS_ORIGINS: list[str] = _parse_cors_origins(
    os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
)

if not CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS must include at least one origin")
if "*" in CORS_ORIGINS:
    raise RuntimeError("CORS_ORIGINS cannot include '*' when credentials are enabled")


UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
