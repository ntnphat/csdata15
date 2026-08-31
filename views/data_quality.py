import streamlit as st

from movie_analytics import charts, metrics
from movie_analytics.auth import require_login
from movie_analytics.etl import data_quality_report
from movie_analytics.ui import get_data, get_raw_data, show_table, source_badge

require_login()

df_all, source = get_data()
source_badge(source)
raw = get_raw_data()

st.title("🧹 Chất lượng dữ liệu / Data quality")
st.caption(
    "Phần này được đặt trước mọi phân tích vì kết luận chỉ đáng tin khi biết rõ "
    "dữ liệu thiếu ở đâu và thiếu theo cách nào."
)

report = data_quality_report(raw)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Số dòng gốc / Raw rows", f"{len(raw):,}")
col_b.metric("Số cột / Columns", f"{raw.shape[1]}")
col_c.metric("Thiếu ngân sách / Missing budget",
             f"{int(raw['budget'].isna().sum()):,}",
             delta=f"{raw['budget'].isna().mean() * 100:.1f}%", delta_color="inverse")
col_d.metric("Phim dùng được cho phân tích tài chính",
             f"{int(df_all['has_financials'].sum()):,}",
             delta=f"{df_all['has_financials'].mean() * 100:.1f}%")

st.divider()

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Tỷ lệ thiếu theo cột")
    st.pyplot(charts.missing_values_chart(report), width="stretch")

with right:
    st.subheader("Bảng chi tiết")
    show_table(report, height=380)

st.divider()

st.subheader("Dữ liệu thiếu có ngẫu nhiên không? / Is the data missing at random?")
st.markdown(
    "Đây là câu hỏi quan trọng nhất của phần này. Nếu 28% phim thiếu ngân sách là "
    "**ngẫu nhiên**, ta chỉ mất độ chính xác. Nếu thiếu **có hệ thống**, mọi kết luận "
    "sẽ bị lệch. Bảng dưới so sánh trực tiếp hai nhóm:"
)

profile = metrics.missing_budget_profile(df_all)
show_table(profile.round(2), height=120)

st.error(
    "**Kết luận: dữ liệu KHÔNG thiếu ngẫu nhiên.** Nhóm thiếu ngân sách có doanh thu "
    "trung vị thấp hơn khoảng 8-9 lần, lượng vote thấp hơn ~6 lần và tỷ lệ phim Mỹ "
    "thấp hơn đáng kể. Đây chính là các phim độc lập, phim ngoài Hollywood, quy mô nhỏ. "
    "Hệ quả: mọi con số tài chính trong báo cáo này phản ánh **phân khúc phim thương mại "
    "có công bố ngân sách**, và có xu hướng **lạc quan hơn** thực tế toàn ngành "
    "(survivorship bias).",
    icon="⚠️",
)

st.divider()

st.subheader("Các lỗi dữ liệu khác đã xử lý / Other issues handled")

mismatch_count = int(df_all["year_mismatch"].sum()) if "year_mismatch" in df_all else 0
st.markdown(
    f"""
| Vấn đề | Quy mô | Cách xử lý |
|---|---|---|
| Cột `year` lệch với năm trong `released` | **{mismatch_count:,} dòng ({mismatch_count / len(df_all) * 100:.1f}%)** | Lấy năm từ `released` làm chuẩn, giữ `year` gốc ở cột `year_reported` để đối chiếu |
| Chuỗi `released` có 3 định dạng khác nhau | 7.668 dòng | Regex tách ngày + quốc gia, thử lần lượt `%B %d, %Y` → `%B %Y` → `%Y` |
| Nhãn phân loại rời rạc (`Not Rated`, `Approved`, `TV-MA`, `X`...) | 12 nhãn | Gom về 6 nhóm có ý nghĩa thương mại trong cột `rating_group` |
| Tiền tệ danh nghĩa trải dài 40 năm | Toàn bộ | Khử lạm phát bằng CPI-U về USD giá thực 2020 |
| Doanh thu là **worldwide gross**, chưa trừ chia rạp và P&A | Toàn bộ | Dùng ngưỡng hòa vốn 2.0x thay vì so sánh `gross > budget` |
"""
)

with st.expander("Vì sao ngưỡng hòa vốn là 2.0x chứ không phải 1.0x?"):
    kpi = metrics.kpi_summary(df_all)
    st.markdown(
        f"""
Cột `gross` là doanh thu phòng vé toàn cầu, **không phải tiền hãng phim nhận được**:

- Rạp chiếu giữ lại khoảng **50%** doanh thu bán vé.
- Chi phí P&A (in ấn & quảng bá) thường xấp xỉ **50-100% ngân sách sản xuất** và
  **không nằm trong** cột `budget`.

Vì vậy một bộ phim chỉ thực sự hòa vốn khi doanh thu phòng vé đạt khoảng **2 lần**
ngân sách sản xuất. Sự khác biệt là rất lớn:

- Theo tiêu chí ngây thơ `gross > budget`: **{kpi['naive_hit_rate']:.1f}%** phim "có lãi".
- Theo ngưỡng thực tế 2.0x: chỉ **{kpi['hit_rate']:.1f}%** phim thực sự hòa vốn.

Chênh lệch khoảng 20 điểm phần trăm này là lý do nhiều phân tích phổ biến trên
Internet đánh giá quá lạc quan về ngành điện ảnh.
        """
    )
