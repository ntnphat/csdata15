"""Thành phần giao diện dùng chung: nạp dữ liệu có cache, bộ lọc, dải KPI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from movie_analytics.constants import BUDGET_LABELS, RATING_ORDER, SEASON_ORDER
from movie_analytics.db import load_dataset
from movie_analytics.etl import load_raw
from movie_analytics.metrics import kpi_summary

FILTER_KEY = "active_filters"


@st.cache_data(show_spinner="Đang nạp dữ liệu...")
def get_data(prefer_supabase: bool = True) -> tuple[pd.DataFrame, str]:
    """Nạp bộ dữ liệu chính, ưu tiên Supabase và tự lùi về file cục bộ."""
    return load_dataset(prefer_supabase=prefer_supabase)


@st.cache_data(show_spinner=False)
def get_raw_data() -> pd.DataFrame:
    """Dữ liệu gốc chưa xử lý, dùng cho phần đánh giá chất lượng dữ liệu."""
    return load_raw()


def money(value: float, decimals: int = 1) -> str:
    """Định dạng số tiền gọn: B / M / K."""
    if value is None or pd.isna(value):
        return "-"
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= size:
            return f"${value / size:,.{decimals}f}{unit}"
    return f"${value:,.0f}"


def sidebar_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bộ lọc dùng chung cho mọi trang, trạng thái được giữ trong session_state."""
    st.sidebar.header("Bộ lọc / Filters")

    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    years = st.sidebar.slider("Giai đoạn / Period", year_min, year_max, (year_min, year_max))

    genres = st.sidebar.multiselect(
        "Thể loại / Genre", sorted(df["genre"].dropna().unique().tolist())
    )
    ratings = st.sidebar.multiselect(
        "Phân loại tuổi / Rating",
        [r for r in RATING_ORDER if r in set(df["rating_group"].dropna())],
    )
    seasons = st.sidebar.multiselect(
        "Mùa phát hành / Season",
        [s for s in SEASON_ORDER if s in set(df["season"].dropna())],
    )
    tiers = st.sidebar.multiselect(
        "Tầng ngân sách / Budget tier",
        [t for t in BUDGET_LABELS if t in set(df["budget_tier"].dropna().astype(str))],
    )

    top_countries = df["country"].value_counts().head(20).index.tolist()
    countries = st.sidebar.multiselect("Quốc gia / Country", top_countries)

    financial_only = st.sidebar.checkbox(
        "Chỉ phim đủ dữ liệu tài chính / Financials only", value=True,
        help="Bỏ chọn để xem cả 2.171 phim thiếu ngân sách - hữu ích khi đánh giá thiên lệch dữ liệu.",
    )

    filters = {
        "years": list(years), "genres": genres, "ratings": ratings,
        "seasons": seasons, "tiers": tiers, "countries": countries,
        "financial_only": financial_only,
    }
    st.session_state[FILTER_KEY] = filters
    return apply_filters(df, filters), filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Áp dụng bộ lọc lên DataFrame gốc."""
    out = df[df["year"].between(*filters["years"])]

    for column, key in [("genre", "genres"), ("rating_group", "ratings"),
                        ("season", "seasons"), ("country", "countries")]:
        if filters.get(key):
            out = out[out[column].isin(filters[key])]

    if filters.get("tiers"):
        out = out[out["budget_tier"].astype(str).isin(filters["tiers"])]
    if filters.get("financial_only"):
        out = out[out["has_financials"]]

    return out


def kpi_row(df: pd.DataFrame) -> None:
    """Dải chỉ số tổng quan hiển thị trên đầu mỗi trang phân tích."""
    kpi = kpi_summary(df)
    cols = st.columns(5)
    cols[0].metric("Số phim / Titles", f"{kpi['titles']:,}")
    cols[1].metric("Ngân sách trung vị / Median budget", money(kpi["median_budget"]))
    cols[2].metric("Doanh thu trung vị / Median gross", money(kpi["median_gross"]))
    cols[3].metric(
        "Bội số thu hồi vốn / Median multiple",
        f"{kpi['median_multiple']:.2f}x" if pd.notna(kpi["median_multiple"]) else "-",
        delta=f"{kpi['median_multiple'] - 2:.2f} so với ngưỡng 2.0x"
        if pd.notna(kpi["median_multiple"]) else None,
    )
    cols[4].metric(
        "Tỷ lệ hòa vốn / Hit rate",
        f"{kpi['hit_rate']:.1f}%" if pd.notna(kpi["hit_rate"]) else "-",
    )


def empty_guard(df: pd.DataFrame, message: str = "Bộ lọc hiện tại không còn dữ liệu. Hãy nới lỏng điều kiện lọc.") -> None:
    """Dừng trang một cách gọn gàng khi bộ lọc trả về rỗng."""
    if df.empty:
        st.warning(message)
        st.stop()


def show_table(df: pd.DataFrame, height: int = 420) -> None:
    """Hiển thị bảng dữ liệu với định dạng số nhất quán."""
    st.dataframe(df, width="stretch", height=height, hide_index=True)


def source_badge(source: str) -> None:
    """Nhãn cho biết dữ liệu đang lấy từ Supabase hay file cục bộ."""
    if source == "supabase":
        st.sidebar.success("Nguồn dữ liệu: Supabase", icon="🗄️")
    else:
        st.sidebar.info("Nguồn dữ liệu: file cục bộ", icon="💾")
