# config.py — загрузка настроек из .env

import os
from pathlib import Path

# Ищем .env в папке telegram_bot и в корне проекта
ENV_DIRS = [
    Path(__file__).resolve().parent,
    Path(__file__).resolve().parent.parent,
]
_env_loaded = False


def _load_dotenv():
    global _env_loaded
    if _env_loaded:
        return
    try:
        from dotenv import load_dotenv
        for d in ENV_DIRS:
            env_file = d / ".env"
            if env_file.is_file():
                load_dotenv(env_file)
                break
    except ImportError:
        pass
    _env_loaded = True


def get_telegram_token() -> str:
    _load_dotenv()
    token = os.environ.get("TELEGRAM_API_TOKEN", "").strip()
    if not token:
        raise ValueError(
            "Не задан TELEGRAM_API_TOKEN. Создайте файл .env в telegram_bot или в корне проекта с содержимым:\n"
            "TELEGRAM_API_TOKEN=ваш_токен_от_BotFather"
        )
    return token


def get_openai_key() -> str:
    _load_dotenv()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "Не задан OPENAI_API_KEY. Добавьте в .env:\nOPENAI_API_KEY=ваш_ключ_openai"
        )
    return key


def get_mcp_base_url() -> str:
    _load_dotenv()
    return os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8765").rstrip("/")
