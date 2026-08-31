"""Trang xếp hạng đạo diễn, diễn viên, hãng phim và các phim tiêu biểu."""

import streamlit as st

from movie_analytics import charts, metrics
from movie_analytics.auth import require_login
from movie_analytics.ui import empty_guard, get_data, show_table, sidebar_filters, source_badge

require_login()

df_all, source = get_data()
source_badge(source)
df, _ = sidebar_filters(df_all)
empty_guard(df)

st.title("🏆 Xếp hạng / Rankings")
st.caption(
    "Xếp hạng theo bội số thu hồi vốn trung vị. Ngưỡng số phim tối thiểu giúp loại "
    "trường hợp may mắn một lần - đây là khác biệt giữa bảng xếp hạng có ý nghĩa "
    "thống kê và bảng xếp hạng gây hiểu nhầm."
)

col_dim, col_min, col_n = st.columns([2, 1, 1])
dimension = col_dim.selectbox(
    "Xếp hạng theo / Rank by",
    options=["director", "star", "company", "writer"],
    format_func=lambda x: {
        "director": "Đạo diễn / Director",
        "star": "Diễn viên chính / Lead star",
        "company": "Hãng phim / Company",
        "writer": "Biên kịch / Writer",
    }[x],
)
min_titles = col_min.number_input("Số phim tối thiểu", min_value=2, max_value=50, value=8)
top_n = col_n.number_input("Số dòng hiển thị", min_value=5, max_value=50, value=15)

table = metrics.top_entities(df, dimension, min_titles=int(min_titles), top_n=int(top_n))

if table.empty:
    st.warning("Không có nhóm nào đạt ngưỡng số phim tối thiểu. Hãy giảm ngưỡng hoặc nới bộ lọc.")
    st.stop()

st.pyplot(
    charts.group_bar(table, dimension, "median_multiple",
                     f"Top {len(table)} theo bội số thu hồi vốn trung vị", fmt="%.2fx"),
    width="stretch",
)
show_table(table.round(2), height=420)

st.divider()

st.subheader("Ảnh hưởng của ngưỡng lọc / Why the threshold matters")
loose = metrics.top_entities(df, dimension, min_titles=1, top_n=5)
strict = metrics.top_entities(df, dimension, min_titles=15, top_n=5)

col_a, col_b = st.columns(2)
with col_a:
    st.caption("Không đặt ngưỡng (min 1 phim) - dễ bị nhiễu bởi may mắn")
    show_table(loose[[dimension, "titles", "median_multiple"]].round(2), height=200)
with col_b:
    st.caption("Ngưỡng chặt (min 15 phim) - phản ánh năng lực ổn định")
    show_table(strict[[dimension, "titles", "median_multiple"]].round(2), height=200)

st.divider()

st.subheader("Phim tiêu biểu / Notable titles")
tab_profit, tab_loss, tab_roi = st.tabs([
    "Lãi lớn nhất / Top profit", "Lỗ nặng nhất / Biggest losses", "ROI cao nhất / Best ROI",
])

columns = ["name", "year", "genre", "budget_real", "gross_real", "profit_real", "multiple", "score"]
fin = metrics.financial_subset(df)

with tab_profit:
    show_table(fin.nlargest(20, "profit_real")[columns].round(2))
with tab_loss:
    show_table(fin.nsmallest(20, "profit_real")[columns].round(2))
with tab_roi:
    # Lọc ngân sách tối thiểu 1 triệu USD để loại các trường hợp ROI ảo do mẫu số quá nhỏ.
    meaningful = fin[fin["budget_real"] >= 1e6]
    show_table(meaningful.nlargest(20, "multiple")[columns].round(2))
    st.caption("Đã loại phim có ngân sách dưới 1 triệu USD vì mẫu số quá nhỏ làm ROI mất ý nghĩa.")
