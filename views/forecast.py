"""Trang mô hình dự báo doanh thu trước phát hành và mô phỏng kịch bản đầu tư."""

import numpy as np
import pandas as pd
import streamlit as st

from movie_analytics import charts, ml
from movie_analytics.auth import require_login
from movie_analytics.constants import SEASON_MAP
from movie_analytics.ui import get_data, money, show_table, source_badge

require_login()

df_all, source = get_data()
source_badge(source)

st.title("🤖 Dự báo doanh thu / Pre-release forecast")
st.caption(
    "Mô hình chỉ dùng thông tin biết được TRƯỚC khi phim ra rạp. Điểm IMDb và số lượt "
    "vote bị loại khỏi biến đầu vào vì chỉ hình thành sau khi phát hành (data leakage)."
)


@st.cache_resource(show_spinner="Đang huấn luyện mô hình...")
def train(split_year: int):
    features = ml.build_features(df_all)
    results = ml.train_models(features, split_year=split_year)
    return features, results


split_year = st.slider(
    "Mốc chia tập huấn luyện / kiểm định", 2005, 2018, ml.SPLIT_YEAR,
    help="Huấn luyện trên phim phát hành TRƯỚC mốc này, kiểm định trên phim SAU mốc - "
         "đúng với thứ tự thời gian của bài toán thực tế.",
)

features, results = train(split_year)
best = max(results, key=lambda r: r.r2)

st.subheader("Kết quả kiểm định / Model evaluation")

metrics_table = pd.DataFrame(
    [
        {
            "Mô hình / Model": r.name,
            "R² (tập kiểm định)": round(r.r2, 3),
            "MAE (log10)": round(r.mae_log, 3),
            "Sai số trung vị (lần)": round(r.median_error_ratio, 2),
            "Số phim huấn luyện": r.n_train,
            "Số phim kiểm định": r.n_test,
        }
        for r in results
    ]
)
show_table(metrics_table, height=120)

col_a, col_b, col_c = st.columns(3)
col_a.metric("Mô hình tốt nhất", best.name)
col_b.metric("R² giải thích được", f"{best.r2 * 100:.1f}%")
col_c.metric("Sai số dự báo trung vị", f"{best.median_error_ratio:.2f}x", delta_color="off")

st.warning(
    f"**Đây là phát hiện quan trọng nhất của phần mô hình.** Với toàn bộ thông tin có "
    f"trước khi phát hành, mô hình chỉ giải thích được **{best.r2 * 100:.0f}%** biến thiên "
    f"doanh thu và sai lệch trung vị khoảng **{best.median_error_ratio:.1f} lần**. "
    f"Nói cách khác: **không thể chọn đúng phim thắng trước khi phát hành**. "
    f"Kết luận này dẫn thẳng tới khuyến nghị quản trị theo danh mục thay vì đặt cược "
    f"vào từng dự án đơn lẻ.",
    icon="🎯",
)

col_left, col_right = st.columns(2, gap="large")
with col_left:
    st.pyplot(charts.prediction_scatter(best.y_test, best.y_pred), width="stretch")
with col_right:
    importance = ml.feature_importance(best, features, split_year=split_year)
    st.pyplot(charts.feature_importance_chart(importance), width="stretch")

st.markdown(
    "**Đọc biểu đồ độ quan trọng:** ngân sách áp đảo mọi biến còn lại. Thành tích quá khứ "
    "của diễn viên chính gần như không đóng góp - bằng chứng định lượng cho thấy "
    "*star power* không phải yếu tố bảo chứng doanh thu như quan niệm phổ biến."
)

st.divider()

# --- Mô phỏng kịch bản ----------------------------------------------------
st.subheader("Mô phỏng kịch bản đầu tư / Scenario simulator")

with st.form("scenario"):
    row1 = st.columns(3)
    budget_musd = row1[0].number_input("Ngân sách (triệu USD)", 1.0, 400.0, 40.0, step=5.0)
    runtime = row1[1].number_input("Thời lượng (phút)", 60, 240, 110)
    year = row1[2].number_input("Năm phát hành", 2015, 2030, 2020)

    row2 = st.columns(3)
    genre = row2[0].selectbox("Thể loại", sorted(features["genre"].dropna().unique()))
    rating_group = row2[1].selectbox("Phân loại tuổi", sorted(features["rating_group"].dropna().unique()))
    month = row2[2].selectbox("Tháng phát hành", list(range(1, 13)), index=5)

    row3 = st.columns(2)
    is_us = row3[0].selectbox("Thị trường sản xuất", ["US", "Non-US"])
    track = row3[1].slider(
        "Thành tích quá khứ của ê-kíp (log10 doanh thu trung bình)", 5.0, 9.5, 7.7, 0.1,
        help="7.0 ≈ 10 triệu USD, 8.0 ≈ 100 triệu USD, 9.0 ≈ 1 tỷ USD.",
    )
    submitted = st.form_submit_button("Chạy dự báo / Run forecast", width="stretch")

if submitted:
    payload = {
        "log_budget": float(np.log10(budget_musd * 1e6)),
        "runtime": float(runtime),
        "year": int(year),
        "release_month": int(month),
        "director_track": track,
        "star_track": track,
        "company_track": track,
        "genre": genre,
        "rating_group": rating_group,
        "season": SEASON_MAP[int(month)],
        "is_us": is_us,
    }
    result = ml.predict_single(best, payload)

    cols = st.columns(4)
    cols[0].metric("Doanh thu dự báo", money(result["gross_real"]))
    cols[1].metric("Bội số thu hồi vốn", f"{result['multiple']:.2f}x")
    cols[2].metric("Khoảng tin cậy dưới", money(result["band_low"]))
    cols[3].metric("Khoảng tin cậy trên", money(result["band_high"]))

    if result["multiple"] >= 2.0:
        st.success(
            f"Kịch bản này vượt ngưỡng hòa vốn 2.0x. Tuy nhiên khoảng dao động "
            f"{money(result['band_low'])} - {money(result['band_high'])} cho thấy mức độ "
            f"bất định vẫn rất lớn.", icon="✅",
        )
    else:
        st.error(
            f"Kịch bản này **không đạt** ngưỡng hòa vốn 2.0x. Cân nhắc giảm ngân sách, "
            f"đổi cửa sổ phát hành sang mùa hè/lễ, hoặc điều chỉnh nhãn phân loại tuổi "
            f"để mở rộng tệp khán giả.", icon="🚨",
        )

    st.caption(
        "Khoảng tin cậy được suy ra từ sai số trung vị của mô hình trên tập kiểm định, "
        "không phải khoảng dự báo thống kê chuẩn. Kết quả chỉ mang tính tham khảo định hướng."
    )
