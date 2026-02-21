import os


def _load_dotenv() -> None:
    root = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("\"").strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        # Ignore .env parsing errors; env vars can still be set externally.
        return


_load_dotenv()

FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK", "").strip()
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "").strip()
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "").strip()
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "").strip()
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "").strip()
FEISHU_BOT_NAME = os.getenv("FEISHU_BOT_NAME", "丸子").strip()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "").strip()
TG_BOT_NAME = os.getenv("TG_BOT_NAME", "").strip()
TG_POLL_TIMEOUT = int(os.getenv("TG_POLL_TIMEOUT", "25"))
TG_POLL_INTERVAL = float(os.getenv("TG_POLL_INTERVAL", "1"))
NOTIFY_CHANNEL = os.getenv("OPENCLAW_NOTIFY", "").strip().lower()
BILI_SESSDATA = os.getenv("BILI_SESSDATA", "").strip()
BILI_COOKIE = os.getenv("BILI_COOKIE", "").strip()

USER_AGENT = os.getenv(
    "OPENCLAW_UA",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
)

REQUEST_TIMEOUT = float(os.getenv("OPENCLAW_TIMEOUT", "10"))
REQUEST_SLEEP = float(os.getenv("OPENCLAW_SLEEP", "0.2"))
REQUEST_RETRIES = int(os.getenv("OPENCLAW_RETRIES", "3"))
REQUEST_BACKOFF = float(os.getenv("OPENCLAW_BACKOFF", "0.6"))

FOLLOWER_MAX = int(os.getenv("OPENCLAW_FOLLOWER_MAX", "10000"))
KEYWORD_DAYS = int(os.getenv("OPENCLAW_KEYWORD_DAYS", "7"))
KEYWORD_TOPK = int(os.getenv("OPENCLAW_KEYWORD_TOPK", "10"))


def _env_bool(key: str, default: bool = True) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


ENABLE_KEYWORD = _env_bool("OPENCLAW_ENABLE_KEYWORD", True)
DEBUG = _env_bool("OPENCLAW_DEBUG", False)
