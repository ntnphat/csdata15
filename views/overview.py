"""Trang tổng quan: KPI, xu hướng theo thời gian và mức độ tập trung lợi nhuận."""

import streamlit as st

from movie_analytics import charts, metrics
from movie_analytics.auth import require_login
from movie_analytics.ui import (
    empty_guard,
    get_data,
    kpi_row,
    show_table,
    sidebar_filters,
    source_badge,
)

require_login()

df_all, source = get_data()
source_badge(source)
df, _ = sidebar_filters(df_all)
empty_guard(df)

st.title("📊 Tổng quan / Overview")
st.caption("Mọi giá trị tiền tệ đã quy về USD giá thực năm 2020 (CPI-U, base 2020).")

kpi_row(df)

kpi = metrics.kpi_summary(df)
st.info(
    f"**Phát hiện nền tảng:** bội số thu hồi vốn trung vị là "
    f"**{kpi['median_multiple']:.2f}x**, trong khi ngưỡng hòa vốn thực tế của ngành "
    f"(sau khi trừ phần chia cho rạp và chi phí P&A) là **2.0x**. "
    f"Chỉ **{kpi['hit_rate']:.1f}%** số phim vượt được ngưỡng này.",
    icon="💡",
)

st.divider()

col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.subheader("Ngân sách vs Doanh thu")
    st.pyplot(charts.budget_vs_gross_scatter(df), width="stretch")
    st.caption(
        "Mỗi điểm là một bộ phim (thang log). Điểm nằm dưới đường đỏ 2x là phim "
        "nhiều khả năng lỗ sau khi tính đầy đủ chi phí phát hành."
    )

with col_right:
    st.subheader("Tập trung lợi nhuận (Pareto)")
    pareto = metrics.pareto_concentration(df)
    st.pyplot(charts.pareto_chart(pareto), width="stretch")
    st.caption(
        "Ngành vận hành theo quy luật hit-driven: một nhóm nhỏ phim gánh gần như "
        "toàn bộ lợi nhuận của cả danh mục."
    )

st.divider()

st.subheader("Diễn biến theo thời gian / Trend over time")
trend = metrics.yearly_trend(df)
st.pyplot(charts.trend_lines(trend), width="stretch")
st.caption(
    "Lưu ý: năm 2020 chỉ có rất ít phim trong dữ liệu (đại dịch COVID-19 và thời "
    "điểm cắt dữ liệu), nên không nên diễn giải điểm cuối như một xu hướng."
)

with st.expander("Bảng số liệu chi tiết theo năm"):
    show_table(trend.round(2))

st.divider()

st.subheader("Phân bố các biến tài chính / Distributions")
tab_budget, tab_gross, tab_multiple = st.tabs(["Ngân sách", "Doanh thu", "Bội số thu hồi vốn"])

with tab_budget:
    st.pyplot(charts.distribution_plot(df, "budget_real", "Phân bố ngân sách (log10)", log=True))
with tab_gross:
    st.pyplot(charts.distribution_plot(df, "gross_real", "Phân bố doanh thu (log10)", log=True))
with tab_multiple:
    clipped = df[df["multiple"].notna() & (df["multiple"] <= 10)]
    st.pyplot(charts.distribution_plot(clipped, "multiple", "Phân bố bội số thu hồi vốn (cắt tại 10x)"))
    st.caption(
        f"Trung vị {kpi['median_multiple']:.2f}x - phân bố lệch phải mạnh, "
        f"nghĩa là số ít phim siêu lãi kéo giá trị trung bình lên và che mất "
        f"thực tế của phần đông còn lại."
    )
