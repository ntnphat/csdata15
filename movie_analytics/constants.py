"""Hằng số dùng chung: đường dẫn, cấu hình cột, bảng CPI, nhóm ngân sách."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
RAW_CSV = DATA_DIR / "movies.csv"
CLEAN_PARQUET = OUTPUT_DIR / "movies_clean.parquet"
CLEAN_CSV = OUTPUT_DIR / "movies_clean.csv"

BASE_YEAR = 2020  # Năm gốc quy đổi tiền tệ về giá thực (real USD)

RAW_COLUMNS = [
    "name", "rating", "genre", "year", "released", "score", "votes",
    "director", "writer", "star", "country", "budget", "gross", "company", "runtime",
]

# Chỉ số giá tiêu dùng Mỹ (CPI-U, all items, annual average, 1982-84 = 100).
# Nguồn: U.S. Bureau of Labor Statistics. Dùng để khử lạm phát cho budget/gross.
CPI_US = {
    1980: 82.4, 1981: 90.9, 1982: 96.5, 1983: 99.6, 1984: 103.9,
    1985: 107.6, 1986: 109.6, 1987: 113.6, 1988: 118.3, 1989: 124.0,
    1990: 130.7, 1991: 136.2, 1992: 140.3, 1993: 144.5, 1994: 148.2,
    1995: 152.4, 1996: 156.9, 1997: 160.5, 1998: 163.0, 1999: 166.6,
    2000: 172.2, 2001: 177.1, 2002: 179.9, 2003: 184.0, 2004: 188.9,
    2005: 195.3, 2006: 201.6, 2007: 207.342, 2008: 215.303, 2009: 214.537,
    2010: 218.056, 2011: 224.939, 2012: 229.594, 2013: 232.957, 2014: 236.736,
    2015: 237.017, 2016: 240.007, 2017: 245.120, 2018: 251.107, 2019: 255.657,
    2020: 258.811,
}

# Gom nhãn phân loại độ tuổi rời rạc về 5 nhóm có ý nghĩa thương mại.
RATING_MAP = {
    "G": "G", "PG": "PG", "PG-13": "PG-13", "R": "R",
    "NC-17": "NC-17/X", "X": "NC-17/X",
    "TV-MA": "R", "TV-14": "PG-13", "TV-PG": "PG", "TV-G": "G", "TV-Y7": "G",
    "Not Rated": "Unrated", "Unrated": "Unrated", "Approved": "Unrated",
}
RATING_ORDER = ["G", "PG", "PG-13", "R", "NC-17/X", "Unrated"]

# Phân tầng ngân sách theo giá thực 2020 (đơn vị: triệu USD).
BUDGET_BINS = [0, 5e6, 20e6, 50e6, 100e6, float("inf")]
BUDGET_LABELS = ["Micro (<5M)", "Low (5-20M)", "Mid (20-50M)", "High (50-100M)", "Blockbuster (>100M)"]

# Mùa phát hành - các cửa sổ phát hành có ý nghĩa trong ngành.
SEASON_MAP = {
    1: "Q1 - Dump months", 2: "Q1 - Dump months", 3: "Spring",
    4: "Spring", 5: "Summer blockbuster", 6: "Summer blockbuster",
    7: "Summer blockbuster", 8: "Late summer", 9: "Fall - Awards",
    10: "Fall - Awards", 11: "Holiday", 12: "Holiday",
}
SEASON_ORDER = ["Q1 - Dump months", "Spring", "Summer blockbuster", "Late summer", "Fall - Awards", "Holiday"]

MIN_TITLES_FOR_RANKING = 5  # Ngưỡng số phim tối thiểu để xếp hạng người/hãng
