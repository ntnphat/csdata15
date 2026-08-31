import streamlit as st

from movie_analytics import ai
from movie_analytics.auth import authed_client, current_user, is_guest, require_login
from movie_analytics.db import fetch_chat, log_chat
from movie_analytics.ui import empty_guard, get_data, sidebar_filters, source_badge

require_login()

df_all, source = get_data()
source_badge(source)
df, _ = sidebar_filters(df_all)
empty_guard(df)

st.title("💬 Trợ lý phân tích AI / AI analyst")
st.caption(
    "Trợ lý trả lời dựa trên các bảng tổng hợp do Pandas tính sẵn từ bộ lọc hiện tại. "
    "Mô hình chỉ diễn giải số liệu, không tự sinh và chạy code trên dữ liệu."
)

if not ai.is_available():
    st.warning(
        "Chưa cấu hình `OPENAI_API_KEY` hoặc chưa cài `langchain-openai`. "
        "Bạn vẫn xem được ngữ cảnh số liệu mà trợ lý sẽ sử dụng ở phần bên dưới.",
        icon="🔑",
    )

context = ai.build_context(df)

with st.expander("Xem ngữ cảnh số liệu trợ lý đang dùng / Inspect the context"):
    st.markdown(context)
    st.caption(f"Độ dài ngữ cảnh: {len(context):,} ký tự.")

st.subheader("Câu hỏi gợi ý / Suggested questions")
cols = st.columns(3)
for index, question in enumerate(ai.SUGGESTED_QUESTIONS):
    if cols[index % 3].button(question, key=f"suggest_{index}", width="stretch"):
        st.session_state["pending_question"] = question

st.divider()

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

for role, message in st.session_state["chat_history"]:
    with st.chat_message(role):
        st.markdown(message)

question = st.chat_input("Đặt câu hỏi về dữ liệu...") or st.session_state.pop("pending_question", None)

if question:
    st.session_state["chat_history"].append(("user", question))
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích..."):
            answer = ai.ask(df, question, context=context)
        st.markdown(answer)

    st.session_state["chat_history"].append(("assistant", answer))

    if not is_guest():
        try:
            log_chat(authed_client(), current_user()["id"], question, answer)
        except Exception:
            pass  # Không để lỗi ghi log làm gián đoạn trải nghiệm hỏi đáp.

st.divider()

col_a, col_b = st.columns([1, 1])

with col_a:
    if st.button("Sinh tóm tắt điều hành / Executive summary", width="stretch"):
        with st.spinner("Đang tổng hợp..."):
            summary = ai.executive_summary(df, context=context)
        st.session_state["exec_summary"] = summary

with col_b:
    if st.button("Xóa hội thoại / Clear chat", width="stretch"):
        st.session_state["chat_history"] = []
        st.rerun()

if st.session_state.get("exec_summary"):
    st.subheader("Tóm tắt điều hành / Executive summary")
    st.markdown(st.session_state["exec_summary"])
    st.caption("Nội dung này sẽ được chèn vào sheet Tóm tắt khi bạn xuất báo cáo Excel.")

if not is_guest():
    with st.expander("Lịch sử hỏi đáp đã lưu trên Supabase"):
        try:
            history = fetch_chat(authed_client(), current_user()["id"])
            if history.empty:
                st.caption("Chưa có lịch sử.")
            else:
                st.dataframe(history, width="stretch", hide_index=True)
        except Exception as exc:
            st.caption(f"Chưa đọc được lịch sử: {exc}")
