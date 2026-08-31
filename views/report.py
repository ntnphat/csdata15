from datetime import datetime

import streamlit as st

from movie_analytics import metrics
from movie_analytics.auth import authed_client, current_user, is_guest, require_login
from movie_analytics.db import delete_view, list_views, save_view
from movie_analytics.export import build_excel_report
from movie_analytics.ui import (
    apply_filters,
    empty_guard,
    get_data,
    get_raw_data,
    kpi_row,
    show_table,
    sidebar_filters,
    source_badge,
)

require_login()

df_all, source = get_data()
source_badge(source)
df, filters = sidebar_filters(df_all)
empty_guard(df)

st.title("📥 Xuất báo cáo / Report export")
kpi_row(df)
st.divider()

st.subheader("Báo cáo Excel nhiều sheet / Multi-sheet Excel report")

col_opt, col_rows = st.columns([2, 1])
include_charts = col_opt.checkbox("Chèn biểu đồ vào file Excel", value=True)
detail_rows = col_rows.number_input("Số dòng dữ liệu chi tiết", 100, 8000, 2000, step=100)

summary_text = st.text_area(
    "Tóm tắt điều hành đưa vào báo cáo / Executive summary",
    value=st.session_state.get("exec_summary", ""),
    height=160,
    placeholder="Tự nhập, hoặc sinh tự động ở trang Trợ lý AI rồi quay lại đây.",
)

st.caption(
    "Báo cáo gồm 12 sheet: tóm tắt, chất lượng dữ liệu, phân tích theo thể loại / "
    "phân loại tuổi / tầng ngân sách / mùa phát hành, xu hướng theo năm, Pareto, "
    "điểm IMDb, xếp hạng, dữ liệu chi tiết và biểu đồ."
)

if st.button("Tạo file Excel / Generate report", type="primary", width="stretch"):
    with st.spinner("Đang dựng báo cáo..."):
        buffer = build_excel_report(
            df,
            raw=get_raw_data(),
            summary_text=summary_text,
            include_charts=include_charts,
            detail_rows=int(detail_rows),
        )
    st.session_state["report_buffer"] = buffer.getvalue()
    st.success("Đã tạo xong báo cáo.")

if st.session_state.get("report_buffer"):
    filename = f"bao_cao_dien_anh_{datetime.now():%Y%m%d_%H%M}.xlsx"
    st.download_button(
        "⬇️ Tải báo cáo Excel",
        data=st.session_state["report_buffer"],
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

st.divider()

st.subheader("Tải dữ liệu thô đã lọc / Filtered dataset")
st.download_button(
    "⬇️ Tải CSV dữ liệu đang lọc",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"movies_filtered_{len(df)}.csv",
    mime="text/csv",
)

st.divider()

st.subheader("Bộ lọc đã lưu / Saved views")

if is_guest():
    st.info("Đăng nhập bằng tài khoản Supabase để lưu lại bộ lọc phân tích.", icon="🔐")
else:
    user = current_user()
    col_name, col_save = st.columns([3, 1])
    view_name = col_name.text_input("Tên bộ lọc", placeholder="VD: Phim kinh dị ngân sách thấp 2010-2020")

    if col_save.button("Lưu / Save", width="stretch"):
        if not view_name.strip():
            st.error("Hãy đặt tên cho bộ lọc.")
        else:
            try:
                save_view(authed_client(), user["id"], view_name.strip(), filters)
                st.success("Đã lưu bộ lọc.")
            except Exception as exc:
                st.error(f"Không lưu được: {exc}")

    try:
        views = list_views(authed_client(), user["id"])
    except Exception as exc:
        views = None
        st.caption(f"Chưa đọc được danh sách bộ lọc: {exc}")

    if views is not None and not views.empty:
        for _, row in views.iterrows():
            with st.container(border=True):
                cols = st.columns([4, 1, 1])
                cols[0].markdown(f"**{row['view_name']}**  \n`{row['filters']}`")
                if cols[1].button("Áp dụng", key=f"apply_{row['id']}", width="stretch"):
                    preview = apply_filters(df_all, row["filters"])
                    st.session_state["preview_view"] = row["view_name"]
                    st.info(f"Bộ lọc **{row['view_name']}** khớp {len(preview):,} phim.")
                if cols[2].button("Xóa", key=f"delete_{row['id']}", width="stretch"):
                    delete_view(authed_client(), row["id"])
                    st.rerun()
    elif views is not None:
        st.caption("Chưa có bộ lọc nào được lưu.")

st.divider()

st.subheader("Xem trước nội dung báo cáo / Report preview")
preview_tabs = st.tabs(["Thể loại", "Tầng ngân sách", "Mùa phát hành", "Pareto", "Xu hướng năm"])

with preview_tabs[0]:
    show_table(metrics.risk_return_table(df, "genre", 20).round(2))
with preview_tabs[1]:
    show_table(metrics.group_performance(df, "budget_tier", 10).round(2))
with preview_tabs[2]:
    show_table(metrics.group_performance(df, "season", 10).round(2))
with preview_tabs[3]:
    show_table(metrics.pareto_concentration(df).round(2))
with preview_tabs[4]:
    show_table(metrics.yearly_trend(df).round(2))
