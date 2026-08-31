import streamlit as st

from movie_analytics.auth import login_as_guest, sign_in, sign_up
from movie_analytics.config import get_settings

settings = get_settings()

st.title("🎬 Movie Investment Analytics")
st.caption(
    "Phân tích hiệu quả tài chính 7.668 bộ phim giai đoạn 1980-2020 "
    "và đề xuất chiến lược phân bổ ngân sách sản xuất."
)

left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Vấn đề đặt ra / The problem")
    st.markdown(
        """
Hơn một nửa số phim có công bố ngân sách **không đạt ngưỡng hòa vốn thực tế**
của ngành. Ứng dụng này trả lời ba câu hỏi:

1. **Yếu tố nào** thực sự quyết định hiệu quả tài chính của một bộ phim?
2. **Vùng ngân sách, thể loại, thời điểm phát hành nào** có rủi ro cao nhất?
3. Một hãng phim nên **phân bổ vốn** ra sao để giảm xác suất thua lỗ?

Toàn bộ giá trị tiền tệ đã được khử lạm phát về **USD giá thực năm 2020** (CPI-U),
nên các so sánh xuyên suốt 40 năm là hợp lệ.
        """
    )

with right:
    st.subheader("Truy cập / Access")

    if not settings.supabase_ready:
        st.warning(
            "Hệ thống tài khoản hiện chưa sẵn sàng. Bạn vẫn có thể vào bằng chế độ "
            "khách để xem toàn bộ phần phân tích.",
            icon="⚠️",
        )

    tab_login, tab_signup = st.tabs(["Đăng nhập / Sign in", "Đăng ký / Sign up"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Mật khẩu / Password", type="password")
            submitted = st.form_submit_button("Đăng nhập", width="stretch")

        if submitted:
            ok, message = sign_in(email.strip(), password)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab_signup:
        with st.form("signup_form"):
            new_name = st.text_input("Họ và tên / Full name")
            new_email = st.text_input("Email đăng ký")
            new_password = st.text_input("Mật khẩu (tối thiểu 6 ký tự)", type="password")
            confirm = st.text_input("Nhập lại mật khẩu", type="password")
            registered = st.form_submit_button("Tạo tài khoản", width="stretch")

        if registered:
            if len(new_password) < 6:
                st.error("Mật khẩu phải có ít nhất 6 ký tự.")
            elif new_password != confirm:
                st.error("Hai lần nhập mật khẩu không khớp.")
            else:
                ok, message = sign_up(new_email.strip(), new_password, new_name.strip())
                (st.success if ok else st.error)(message)

    st.divider()
    if st.button("Vào bằng chế độ khách / Continue as guest", width="stretch"):
        login_as_guest()
        st.rerun()
