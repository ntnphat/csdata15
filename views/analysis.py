"""Trang phân tích chuyên sâu: thể loại, ngân sách, phân loại tuổi, mùa, chất lượng."""

import streamlit as st

from movie_analytics import charts, metrics
from movie_analytics.auth import require_login
from movie_analytics.constants import BUDGET_LABELS, RATING_ORDER, SEASON_ORDER
from movie_analytics.ui import empty_guard, get_data, kpi_row, show_table, sidebar_filters, source_badge

require_login()

df_all, source = get_data()
source_badge(source)
df, _ = sidebar_filters(df_all)
empty_guard(df)

st.title("🔍 Phân tích chuyên sâu / Deep dive")
kpi_row(df)
st.divider()

tabs = st.tabs([
    "Thể loại / Genre",
    "Ngân sách / Budget",
    "Phân loại tuổi / Rating",
    "Mùa phát hành / Season",
    "Chất lượng vs Tiền / Quality",
    "Tương quan / Correlation",
])

# --- Thể loại -------------------------------------------------------------
with tabs[0]:
    st.subheader("Bản đồ rủi ro - lợi nhuận theo thể loại")
    risk = metrics.risk_return_table(df, "genre", min_count=20)
    if risk.empty:
        st.warning("Không đủ dữ liệu sau khi lọc để phân tích theo thể loại.")
    else:
        st.pyplot(charts.risk_return_scatter(risk), width="stretch")
        st.markdown(
            "**Cách đọc:** góc trên bên trái là vùng lý tưởng - lợi nhuận cao, tỷ lệ lỗ thấp. "
            "Cỡ bóng thể hiện ngân sách trung vị, cho thấy quy mô vốn phải bỏ ra."
        )
        st.pyplot(
            charts.boxplot_by_group(df, "genre", "multiple",
                                    "Phân bố bội số thu hồi vốn theo thể loại (cắt tại 10x)"),
            width="stretch",
        )
        show_table(risk.round(2), height=340)

# --- Ngân sách ------------------------------------------------------------
with tabs[1]:
    st.subheader("Hiệu quả theo tầng ngân sách")
    tier = metrics.group_performance(df, "budget_tier", min_count=10)
    if tier.empty:
        st.warning("Không đủ dữ liệu sau khi lọc.")
    else:
        order = [t for t in BUDGET_LABELS if t in set(tier["budget_tier"].astype(str))]
        tier_ordered = tier.set_index("budget_tier").reindex(order).reset_index()
        st.pyplot(
            charts.group_bar(tier_ordered, "budget_tier", "median_multiple",
                             "Bội số thu hồi vốn trung vị theo tầng ngân sách",
                             ylabel="Bội số (x)", fmt="%.2fx"),
            width="stretch",
        )
        st.pyplot(
            charts.group_bar(tier_ordered, "budget_tier", "hit_rate",
                             "Tỷ lệ đạt ngưỡng hòa vốn 2x theo tầng ngân sách",
                             ylabel="% phim hòa vốn", fmt="%.1f%%", color=charts.WARN),
            width="stretch",
        )
        st.warning(
            "**Đường cong hình chữ U:** phim siêu nhỏ và phim bom tấn đều hiệu quả, "
            "còn nhóm ngân sách trung bình 20-50 triệu USD là vùng rủi ro nhất - đủ đắt "
            "để lỗ nặng nhưng không đủ lớn để tạo sự kiện phòng vé.",
            icon="⚠️",
        )
        show_table(tier_ordered.round(2), height=250)

# --- Phân loại tuổi -------------------------------------------------------
with tabs[2]:
    st.subheader("Hiệu quả theo nhãn phân loại độ tuổi")
    rating = metrics.group_performance(df, "rating_group", min_count=10)
    if rating.empty:
        st.warning("Không đủ dữ liệu sau khi lọc.")
    else:
        order = [r for r in RATING_ORDER if r in set(rating["rating_group"])]
        rating_ordered = rating.set_index("rating_group").reindex(order).reset_index()
        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(charts.group_bar(rating_ordered, "rating_group", "median_multiple",
                                       "Bội số thu hồi vốn trung vị", fmt="%.2fx"))
        with col2:
            st.pyplot(charts.group_bar(rating_ordered, "rating_group", "mean_score",
                                       "Điểm IMDb trung bình", fmt="%.2f", color=charts.WARN))
        st.info(
            "**Nghịch lý chất lượng - thương mại:** phim nhãn R thường được đánh giá cao hơn "
            "nhưng lại có bội số thu hồi vốn thấp nhất, do nhãn R cắt bỏ nhóm khán giả "
            "gia đình và tuổi teen - phân khúc quyết định doanh thu phòng vé.",
            icon="🎭",
        )
        show_table(rating_ordered.round(2), height=250)

# --- Mùa phát hành --------------------------------------------------------
with tabs[3]:
    st.subheader("Hiệu quả theo cửa sổ phát hành")
    season = metrics.group_performance(df, "season", min_count=10)
    if season.empty:
        st.warning("Không đủ dữ liệu sau khi lọc.")
    else:
        order = [s for s in SEASON_ORDER if s in set(season["season"])]
        season_ordered = season.set_index("season").reindex(order).reset_index()
        st.pyplot(
            charts.group_bar(season_ordered, "season", "median_multiple",
                             "Bội số thu hồi vốn trung vị theo mùa phát hành", fmt="%.2fx"),
            width="stretch",
        )
        st.markdown(
            "Mùa hè và dịp lễ cuối năm vượt trội. Mùa thu - giai đoạn phim tranh giải - "
            "có bội số thấp nhất: đây là cửa sổ tối ưu cho uy tín nghệ thuật, không phải "
            "cho lợi nhuận."
        )
        show_table(season_ordered.round(2), height=250)

# --- Chất lượng vs tiền ---------------------------------------------------
with tabs[4]:
    st.subheader("Điểm IMDb có đi cùng lợi nhuận không?")
    bands = metrics.score_vs_money(df)
    if bands.empty:
        st.warning("Không đủ dữ liệu sau khi lọc.")
    else:
        st.pyplot(
            charts.group_bar(bands, "score_band", "median_multiple",
                             "Bội số thu hồi vốn theo dải điểm IMDb",
                             fmt="%.2fx", horizontal=False),
            width="stretch",
        )
        show_table(bands.round(2), height=230)
        st.info(
            "Quan hệ **phi tuyến**: hệ số tương quan tuyến tính giữa điểm số và doanh thu "
            "chỉ ở mức yếu, nhưng khi chia theo dải điểm thì nhóm 8-10 điểm vượt trội hẳn. "
            "Lưu ý nhân quả hai chiều: phim hay kéo khán giả, nhưng phim ăn khách cũng thu "
            "hút nhiều lượt đánh giá tích cực hơn.",
            icon="🧠",
        )

# --- Tương quan -----------------------------------------------------------
with tabs[5]:
    st.subheader("Ma trận tương quan giữa các biến định lượng")
    corr = metrics.correlation_matrix(df)
    st.pyplot(charts.correlation_heatmap(corr), width="stretch")
    st.markdown(
        """
**Ba điểm đáng chú ý:**

- `budget` ↔ `gross` tương quan mạnh: tiền bỏ ra dự báo được doanh thu, nhưng
  **không** đảm bảo tỷ suất sinh lời.
- `score` ↔ `budget` gần như bằng 0: **không mua được chất lượng bằng tiền**.
- `votes` ↔ `gross` cao, song đây là biến chỉ có **sau** khi phim ra rạp nên không
  dùng được cho dự báo trước phát hành.
        """
    )
