"""Tầng dữ liệu: kết nối Supabase, nạp dữ liệu phim và lưu trạng thái người dùng.

App luôn chạy được: nếu chưa cấu hình Supabase thì tự động lùi về dữ liệu cục bộ.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from movie_analytics.config import get_settings
from movie_analytics.constants import CLEAN_CSV, CLEAN_PARQUET
from movie_analytics.etl import build_dataset

MOVIES_TABLE = "movies"
VIEWS_TABLE = "saved_views"
CHAT_TABLE = "chat_logs"
PROFILES_TABLE = "profiles"

# Các cột được đồng bộ lên Supabase (bỏ cột trung gian chỉ dùng khi tính toán).
SYNC_COLUMNS = [
    "name", "rating", "rating_group", "genre", "year", "year_reported", "release_date",
    "release_month", "season", "decade", "score", "votes", "director", "writer", "star",
    "country", "company", "runtime", "budget", "gross", "budget_real", "gross_real",
    "profit_real", "multiple", "roi", "has_financials", "is_profitable_real", "budget_tier",
]


class SupabaseUnavailable(RuntimeError):
    """Không có thư viện supabase hoặc thiếu thông tin kết nối."""


def get_client(use_service_key: bool = False):
    """Khởi tạo Supabase client. Ném SupabaseUnavailable nếu chưa sẵn sàng."""
    settings = get_settings()
    if not settings.supabase_ready:
        raise SupabaseUnavailable("Chưa cấu hình SUPABASE_URL / SUPABASE_ANON_KEY.")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise SupabaseUnavailable("Chưa cài đặt thư viện supabase.") from exc

    key = settings.supabase_service_key if use_service_key else settings.supabase_anon_key
    return create_client(settings.supabase_url, key or settings.supabase_anon_key)


def is_supabase_ready() -> bool:
    try:
        get_client()
        return True
    except SupabaseUnavailable:
        return False


# --- Dữ liệu phim ---------------------------------------------------------

def _prepare_for_upload(df: pd.DataFrame) -> list[dict]:
    """Chuẩn hóa DataFrame thành list dict tương thích kiểu JSON của PostgREST."""
    out = df[[c for c in SYNC_COLUMNS if c in df.columns]].copy()
    out["release_date"] = out["release_date"].dt.strftime("%Y-%m-%d")
    out["budget_tier"] = out["budget_tier"].astype("string")
    out = out.astype(object).where(pd.notna(out), None)
    return json.loads(json.dumps(out.to_dict(orient="records"), default=str))


def upload_movies(df: pd.DataFrame, batch_size: int = 500) -> int:
    """Load: đẩy dữ liệu đã làm sạch lên bảng movies theo từng lô."""
    client = get_client(use_service_key=True)
    records = _prepare_for_upload(df)

    client.table(MOVIES_TABLE).delete().neq("name", "").execute()
    for start in range(0, len(records), batch_size):
        client.table(MOVIES_TABLE).insert(records[start:start + batch_size]).execute()
    return len(records)


def fetch_movies_from_supabase(page_size: int = 1000) -> pd.DataFrame:
    """Đọc toàn bộ bảng movies, phân trang vì PostgREST giới hạn số dòng mỗi lần."""
    client = get_client()
    frames, start = [], 0
    while True:
        response = client.table(MOVIES_TABLE).select("*").range(start, start + page_size - 1).execute()
        rows = response.data or []
        if not rows:
            break
        frames.append(pd.DataFrame(rows))
        if len(rows) < page_size:
            break
        start += page_size

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    return df


def load_local_dataset() -> pd.DataFrame:
    """Đọc bản sạch trong outputs/, tự chạy lại ETL nếu chưa có."""
    if CLEAN_PARQUET.exists():
        try:
            return pd.read_parquet(CLEAN_PARQUET)
        except (ImportError, ValueError):
            pass
    if CLEAN_CSV.exists():
        df = pd.read_csv(CLEAN_CSV)
        df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
        return df
    return build_dataset(save=True)


def load_dataset(prefer_supabase: bool = True) -> tuple[pd.DataFrame, str]:
    """Nạp dữ liệu cho toàn app. Trả về (DataFrame, nguồn dữ liệu)."""
    if prefer_supabase:
        try:
            df = fetch_movies_from_supabase()
            if not df.empty:
                return df, "supabase"
        except Exception:
            pass
    return load_local_dataset(), "local"


# --- Trạng thái người dùng ------------------------------------------------

def save_view(client, user_id: str, name: str, filters: dict[str, Any]) -> None:
    """Lưu một bộ lọc phân tích của người dùng."""
    client.table(VIEWS_TABLE).insert(
        {"user_id": user_id, "view_name": name, "filters": filters}
    ).execute()


def list_views(client, user_id: str) -> pd.DataFrame:
    response = (
        client.table(VIEWS_TABLE)
        .select("id, view_name, filters, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def delete_view(client, view_id: str) -> None:
    client.table(VIEWS_TABLE).delete().eq("id", view_id).execute()


def log_chat(client, user_id: str, question: str, answer: str) -> None:
    """Ghi lại hội thoại với trợ lý AI để phục vụ đánh giá chất lượng."""
    client.table(CHAT_TABLE).insert(
        {"user_id": user_id, "question": question, "answer": answer}
    ).execute()


def fetch_chat(client, user_id: str, limit: int = 50) -> pd.DataFrame:
    response = (
        client.table(CHAT_TABLE)
        .select("question, answer, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def upsert_profile(client, user_id: str, email: str, full_name: str = "") -> None:
    client.table(PROFILES_TABLE).upsert(
        {"id": user_id, "email": email, "full_name": full_name}
    ).execute()
