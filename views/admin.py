import streamlit as st

from movie_analytics.auth import require_admin
from movie_analytics.config import get_settings
from movie_analytics.constants import CLEAN_CSV, RAW_CSV
from movie_analytics.db import SupabaseUnavailable, fetch_movies_from_supabase, upload_movies
from movie_analytics.etl import build_dataset, data_quality_report, load_raw
from movie_analytics.ui import get_data, get_raw_data, show_table

require_admin()
settings = get_settings()

st.title("⚙️ Quản trị dữ liệu / Data admin")
st.caption("Vận hành pipeline ETL: Extract từ CSV → Transform bằng Pandas → Load lên Supabase.")

st.subheader("Trạng thái hệ thống / System status")

cols = st.columns(4)
cols[0].metric("File nguồn", "Sẵn sàng" if RAW_CSV.exists() else "Thiếu")
cols[1].metric("Bản đã làm sạch", "Có" if CLEAN_CSV.exists() else "Chưa tạo")
cols[2].metric("Supabase", "Đã cấu hình" if settings.supabase_ready else "Chưa cấu hình")
cols[3].metric("OpenAI", "Đã cấu hình" if settings.openai_ready else "Chưa cấu hình")

if not settings.supabase_ready:
    st.info(
        "Điền `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` vào file `.env` "
        "(chạy máy cá nhân) hoặc `.streamlit/secrets.toml` (Streamlit Cloud) để bật đồng bộ.",
        icon="ℹ️",
    )

st.divider()

st.subheader("Bước 1 - Extract & Transform")

if st.button("Chạy lại pipeline làm sạch dữ liệu", width="stretch"):
    with st.spinner("Đang xử lý..."):
        cleaned = build_dataset(save=True)
    st.cache_data.clear()
    st.success(
        f"Đã xử lý {len(cleaned):,} dòng, {cleaned.shape[1]} cột. "
        f"Bản sạch được ghi vào `outputs/`."
    )

with st.expander("Xem báo cáo chất lượng dữ liệu nguồn"):
    show_table(data_quality_report(get_raw_data()), height=420)

with st.expander("Xem 20 dòng dữ liệu gốc"):
    show_table(load_raw().head(20))

st.divider()

st.subheader("Bước 2 - Load lên Supabase")

st.warning(
    "Thao tác này **xóa toàn bộ** bảng `movies` trên Supabase rồi nạp lại từ đầu. "
    "Cần `SUPABASE_SERVICE_KEY` và bảng đã được tạo bằng `sql/schema.sql`.",
    icon="⚠️",
)

confirm = st.checkbox("Tôi hiểu và muốn ghi đè bảng movies trên Supabase")

if st.button("Đồng bộ dữ liệu lên Supabase", disabled=not confirm, width="stretch"):
    df_local, _ = get_data(prefer_supabase=False)
    try:
        with st.spinner("Đang tải lên..."):
            rows = upload_movies(df_local)
        st.cache_data.clear()
        st.success(f"Đã nạp {rows:,} dòng lên bảng `movies`.")
    except SupabaseUnavailable as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Đồng bộ thất bại: {exc}")

if st.button("Kiểm tra dữ liệu trên Supabase", width="stretch"):
    try:
        remote = fetch_movies_from_supabase()
        if remote.empty:
            st.warning("Bảng `movies` trên Supabase đang rỗng.")
        else:
            st.success(f"Đọc được {len(remote):,} dòng từ Supabase.")
            show_table(remote.head(20))
    except SupabaseUnavailable as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Không đọc được: {exc}")

st.divider()

st.subheader("Hướng dẫn thiết lập Supabase / Setup guide")
st.markdown(
    """
1. Tạo project tại [supabase.com](https://supabase.com) (Free tier là đủ cho đề án).
2. Vào **SQL Editor → New query**, dán toàn bộ nội dung `sql/schema.sql` và chạy.
3. Vào **Project Settings → API**, sao chép:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_KEY` (**tuyệt đối không đưa lên GitHub**)
4. Vào **Authentication → Providers → Email**, bật Email provider. Trong lúc phát triển
   có thể tắt *Confirm email* để đăng ký xong dùng được ngay.
5. Điền các khóa vào `.env` rồi quay lại trang này chạy **Bước 2**.
    """
)
