"""
LOI Generator — Streamlit Page (placeholder)
=============================================
Replace this file with the actual LOI Generator logic.
"""

import streamlit as st

st.set_page_config(
    page_title="LOI Generator — Casco Energy",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .main { background-color: #f7f6f2; }
    .page-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-color);
        border-bottom: 2px solid var(--text-color);
        padding-bottom: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📄 LOI Generator</div>', unsafe_allow_html=True)

st.info("🚧 Paste your existing LOI Generator code here to integrate it into the hub.")
