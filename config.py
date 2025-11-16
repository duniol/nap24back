import os
from dotenv import load_dotenv

load_dotenv()


def _to_bool(val, default=False):
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}


class Config:
    """
    Global app config
    """
    FLASK_HOST = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    FLASK_PORT = os.getenv("FLASK_RUN_PORT", "5000")

    # Optional explicit base URL for contexts without a request (CRON etc.)
    BASE_URL = os.getenv("BASE_URL", "")  # e.g. "https://nap24back.vercel.app"

    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_TTL", "600"))
    TMDB_KEY = os.getenv("TMDB_KEY", "")

    DEBUG = _to_bool(os.getenv("FLASK_DEBUG", None), default=False)

    # Helps url_for(_external=True) choose scheme locally
    PREFERRED_URL_SCHEME = "http" if DEBUG else "https"
