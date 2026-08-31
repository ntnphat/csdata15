"""ETL: đọc CSV thô -> làm sạch -> tạo biến phái sinh -> lưu bản sạch.

Pipeline theo mô hình Extract - Transform - Load đã học ở buổi 12.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from movie_analytics.constants import (
    BASE_YEAR,
    BUDGET_BINS,
    BUDGET_LABELS,
    CLEAN_CSV,
    CLEAN_PARQUET,
    CPI_US,
    OUTPUT_DIR,
    RATING_MAP,
    RAW_CSV,
    SEASON_MAP,
)

# "June 13, 1980 (United States)" -> ngày phát hành + quốc gia phát hành
RELEASED_PATTERN = re.compile(r"^\s*(?P<date>[^()]+?)\s*(?:\((?P<country>[^()]*)\))?\s*$")

TEXT_COLUMNS = ["name", "rating", "genre", "director", "writer", "star", "country", "company"]

# Ngưỡng hòa vốn thực tế của ngành: doanh thu phòng vé bị chia cho rạp (~50%)
# và chi phí P&A xấp xỉ 50% ngân sách sản xuất => cần ~2.0x budget mới hòa vốn.
BREAKEVEN_MULTIPLE = 2.0


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Extract: đọc dữ liệu gốc, không chỉnh sửa."""
    return pd.read_csv(path)


def _parse_released(value):
    """Tách chuỗi released thành (ngày phát hành, quốc gia phát hành)."""
    if not isinstance(value, str) or not value.strip():
        return pd.NaT, np.nan

    match = RELEASED_PATTERN.match(value)
    if match is None:
        return pd.NaT, np.nan

    raw_date = (match.group("date") or "").strip().rstrip(",")
    country = (match.group("country") or "").strip() or np.nan

    # Ba định dạng gặp trong dữ liệu: đủ ngày, chỉ tháng-năm, chỉ năm.
    for fmt in ("%B %d, %Y", "%B %Y", "%Y"):
        try:
            return pd.to_datetime(raw_date, format=fmt), country
        except (ValueError, TypeError):
            continue
    return pd.NaT, country


def _deflate(amount: pd.Series, year: pd.Series) -> pd.Series:
    """Quy đổi USD danh nghĩa về giá thực năm gốc bằng chỉ số CPI-U."""
    base_cpi = CPI_US[BASE_YEAR]
    cpi = year.map(CPI_US)
    return amount * (base_cpi / cpi)


def data_quality_report(raw: pd.DataFrame) -> pd.DataFrame:
    """Bảng thống kê chất lượng dữ liệu trước khi làm sạch."""
    total = len(raw)
    report = pd.DataFrame(
        {
            "Cột / Column": raw.columns,
            "Kiểu / Dtype": [str(t) for t in raw.dtypes],
            "Thiếu / Missing": raw.isna().sum().to_numpy(),
            "Số giá trị duy nhất / Unique": raw.nunique(dropna=True).to_numpy(),
        }
    )
    report["% thiếu / % missing"] = (report["Thiếu / Missing"] / total * 100).round(2)
    return report.sort_values("% thiếu / % missing", ascending=False, ignore_index=True)


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform: chuẩn hóa kiểu dữ liệu và sinh các biến phân tích."""
    df = raw.copy()

    for col in TEXT_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    # Loại bản ghi trùng hoàn toàn về danh tính phim.
    df = df.drop_duplicates(subset=["name", "year", "director"], keep="first")

    parsed = df["released"].map(_parse_released)
    df["release_date"] = pd.to_datetime([p[0] for p in parsed])
    df["release_country"] = pd.Series([p[1] for p in parsed], index=df.index, dtype="string")

    # Cột `year` trong dữ liệu gốc lệch với năm phát hành thực tế ở nhiều dòng.
    # Ưu tiên năm lấy từ `released`, chỉ dùng `year` khi không parse được.
    release_year = df["release_date"].dt.year
    df["year_reported"] = df["year"]
    df["year"] = release_year.fillna(df["year"]).astype("int64")
    df["year_mismatch"] = release_year.notna() & (release_year != df["year_reported"])

    df["release_month"] = df["release_date"].dt.month
    df["season"] = df["release_month"].map(SEASON_MAP).astype("string")
    df["decade"] = (df["year"] // 10 * 10).astype("int64")

    df["rating_group"] = df["rating"].map(RATING_MAP).fillna("Unrated").astype("string")

    for col in ["budget", "gross", "score", "votes", "runtime"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ngoài phạm vi CPI thì không quy đổi được -> loại khỏi tập phân tích.
    df = df[df["year"].between(min(CPI_US), max(CPI_US))]

    df["budget_real"] = _deflate(df["budget"], df["year"])
    df["gross_real"] = _deflate(df["gross"], df["year"])
    df["profit_real"] = df["gross_real"] - df["budget_real"]
    df["multiple"] = df["gross_real"] / df["budget_real"]
    df["roi"] = df["profit_real"] / df["budget_real"]

    df["has_financials"] = df["budget_real"].notna() & df["gross_real"].notna()
    df["is_profitable_naive"] = df["multiple"] > 1
    df["is_profitable_real"] = df["multiple"] >= BREAKEVEN_MULTIPLE

    df["budget_tier"] = pd.cut(df["budget_real"], bins=BUDGET_BINS, labels=BUDGET_LABELS, right=False)

    df["log_budget"] = np.log10(df["budget_real"])
    df["log_gross"] = np.log10(df["gross_real"])
    df["log_votes"] = np.log10(df["votes"].where(df["votes"] > 0))

    return df.reset_index(drop=True)


def build_dataset(save: bool = True) -> pd.DataFrame:
    """Chạy toàn bộ pipeline và (tùy chọn) ghi bản sạch ra outputs/."""
    df = clean(load_raw())
    if save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(CLEAN_CSV, index=False, encoding="utf-8-sig")
        try:
            df.to_parquet(CLEAN_PARQUET, index=False)
        except (ImportError, ValueError):
            pass  # Không có pyarrow thì dùng CSV là đủ.
    return df


if __name__ == "__main__":
    data = build_dataset()
    print(f"Rows: {len(data):,} | Columns: {data.shape[1]}")
    print(f"Rows with full financials: {int(data['has_financials'].sum()):,}")
