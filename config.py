import os

META_API_VERSION = os.getenv("META_API_VERSION", "v24.0")
GRAPH_BASE_URL = f"https://graph.facebook.com/{META_API_VERSION}"
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID", "").strip()
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
LATE_GRACE_MINUTES = int(os.getenv("LATE_GRACE_MINUTES", "15"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


def require_meta_config():
    missing = []
    if not INSTAGRAM_USER_ID:
        missing.append("INSTAGRAM_USER_ID")
    if not INSTAGRAM_ACCESS_TOKEN:
        missing.append("INSTAGRAM_ACCESS_TOKEN")
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))
