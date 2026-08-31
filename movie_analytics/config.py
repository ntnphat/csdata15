from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv là tùy chọn khi chạy trên Streamlit Cloud
    pass


def _is_placeholder(value: str) -> bool:
    return value.endswith("...") or "xxxx" in value.lower()


def _read(key: str, default: str = "") -> str:
    value = default
    try:
        import streamlit as st

        if key in st.secrets:
            value = str(st.secrets[key])
    except Exception:
        pass
    if value == default:
        value = os.getenv(key, default)
    return "" if _is_placeholder(value) else value


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    openai_embedding_model: str
    app_env: str

    @property
    def supabase_ready(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def openai_ready(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        supabase_url=_read("SUPABASE_URL"),
        supabase_anon_key=_read("SUPABASE_ANON_KEY"),
        supabase_service_key=_read("SUPABASE_SERVICE_KEY"),
        openai_api_key=_read("OPENAI_API_KEY"),
        openai_base_url=_read("OPENAI_BASE_URL"),
        openai_model=_read("OPENAI_MODEL", "gpt-4o-mini"),
        openai_embedding_model=_read("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        app_env=_read("APP_ENV", "local"),
    )
