import streamlit as st


def require_auth():
    if not st.session_state.get("authenticated", False):
        st.warning("Please sign in first.")
        st.switch_page("app.py")
        st.stop()