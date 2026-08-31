from __future__ import annotations

import streamlit as st

from movie_analytics.auth import current_user, sign_out
from movie_analytics.config import get_settings

st.set_page_config(
    page_title="Movie Investment Analytics",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = [
    ("views/overview.py", "Tổng quan / Overview", "📊"),
    ("views/data_quality.py", "Chất lượng dữ liệu / Data quality", "🧹"),
    ("views/analysis.py", "Phân tích chuyên sâu / Deep dive", "🔍"),
    ("views/rankings.py", "Xếp hạng / Rankings", "🏆"),
    ("views/forecast.py", "Dự báo doanh thu / Forecast", "🤖"),
    ("views/ai_analyst.py", "Trợ lý AI / AI analyst", "💬"),
    ("views/report.py", "Xuất báo cáo / Report", "📥"),
    ("views/admin.py", "Quản trị dữ liệu / Admin", "⚙️"),
]


def _sidebar_account() -> None:
    user = current_user()
    if not user:
        return

    st.sidebar.divider()
    label = user.get("full_name") or user["email"]
    st.sidebar.caption(f"Đang đăng nhập: **{label}**")
    if user.get("is_guest"):
        st.sidebar.caption("Chế độ khách - không lưu được dữ liệu cá nhân.")
    if st.sidebar.button("Đăng xuất / Sign out", width="stretch"):
        sign_out()
        st.rerun()


def main() -> None:
    settings = get_settings()

    if current_user() is None:
        pages = [st.Page("views/login.py", title="Đăng nhập / Sign in", icon="🔐", default=True)]
    else:
        pages = [
            st.Page(path, title=title, icon=icon, default=(index == 0))
            for index, (path, title, icon) in enumerate(PAGES)
        ]

    navigation = st.navigation(pages)
    _sidebar_account()

    if current_user() and not settings.supabase_ready:
        st.sidebar.warning("Chưa cấu hình Supabase - app đang chạy trên dữ liệu cục bộ.", icon="⚠️")

    navigation.run()


main()
