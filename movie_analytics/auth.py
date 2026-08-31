from __future__ import annotations

import streamlit as st

from movie_analytics.db import SupabaseUnavailable, get_client, upsert_profile

SESSION_USER = "auth_user"
SESSION_TOKEN = "auth_token"
GUEST_USER = {"id": "guest", "email": "guest@local", "full_name": "Khách / Guest", "is_guest": True}


def current_user() -> dict | None:
    return st.session_state.get(SESSION_USER)


def is_guest() -> bool:
    user = current_user()
    return bool(user and user.get("is_guest"))


def login_as_guest() -> None:
    st.session_state[SESSION_USER] = dict(GUEST_USER)
    st.session_state.pop(SESSION_TOKEN, None)


def sign_up(email: str, password: str, full_name: str = "") -> tuple[bool, str]:
    try:
        client = get_client()
        response = client.auth.sign_up(
            {"email": email, "password": password, "options": {"data": {"full_name": full_name}}}
        )
    except SupabaseUnavailable as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Đăng ký thất bại: {exc}"

    if response.user is None:
        return False, "Đăng ký thất bại. Vui lòng kiểm tra lại email/mật khẩu."
    return True, "Đăng ký thành công. Hãy xác nhận email (nếu được bật) rồi đăng nhập."


def sign_in(email: str, password: str) -> tuple[bool, str]:
    try:
        client = get_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
    except SupabaseUnavailable as exc:
        return False, str(exc)
    except Exception as exc:
        return False, f"Đăng nhập thất bại: {exc}"

    if response.session is None or response.user is None:
        return False, "Sai email hoặc mật khẩu."

    metadata = response.user.user_metadata or {}
    st.session_state[SESSION_USER] = {
        "id": response.user.id,
        "email": response.user.email,
        "full_name": metadata.get("full_name", ""),
        "is_guest": False,
    }
    st.session_state[SESSION_TOKEN] = response.session.access_token

    try:
        upsert_profile(authed_client(), response.user.id, response.user.email,
                       metadata.get("full_name", ""))
    except Exception:
        pass

    return True, "Đăng nhập thành công."


def sign_out() -> None:
    try:
        get_client().auth.sign_out()
    except Exception:
        pass
    st.session_state.pop(SESSION_USER, None)
    st.session_state.pop(SESSION_TOKEN, None)


def authed_client():
    client = get_client()
    token = st.session_state.get(SESSION_TOKEN)
    if token:
        client.postgrest.auth(token)
    return client


def require_login() -> dict:
    user = current_user()
    if user is None:
        st.warning("Vui lòng đăng nhập để sử dụng chức năng này.")
        st.stop()
    return user


def require_account() -> dict:
    user = require_login()
    if user.get("is_guest"):
        st.info("Chức năng này cần tài khoản Supabase. Bạn đang ở chế độ khách.")
        st.stop()
    return user
