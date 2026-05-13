"""
Casco Energy Group — Client Hub
================================
Main entry point. Streamlit automatically picks up pages/ folder
and renders the sidebar navigation.

Run:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Casco Energy Group — Client Hub",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styling — uses CSS variables so it works in both light and dark mode
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Login form */
    .login-wrapper {
        max-width: 380px;
        margin: 0rem auto 0 auto;
        padding: 1rem;
        border: 1px solid var(--secondary-background-color);
        border-radius: 10px;
    }
    .login-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-color);
        margin-bottom: 0.25rem;
    }
    .login-subtitle {
        font-size: 0.85rem;
        color: var(--text-color);
        opacity: 0.5;
        margin-bottom: 1rem;
    }

    /* Cards */
    .app-card {
        background: var(--background-color);
        border: 1px solid var(--secondary-background-color);
        border-radius: 8px;
        padding: 2rem;
        transition: box-shadow 0.2s, transform 0.2s;
        cursor: pointer;
        height: 100%;
    }
    .app-card:hover {
        box-shadow: 4px 4px 0px var(--text-color);
        transform: translate(-2px, -2px);
    }
    .app-card .icon { font-size: 2rem; margin-bottom: 0.75rem; }
    .app-card h3 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-color);
        margin: 0 0 0.5rem 0;
    }
    .app-card p {
        font-size: 0.875rem;
        color: var(--text-color);
        opacity: 0.7;
        line-height: 1.5;
        margin: 0;
    }
    .app-card .tag {
        display: inline-block;
        margin-top: 1rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        background: var(--secondary-background-color);
        color: var(--text-color);
        padding: 2px 8px;
        border-radius: 20px;
    }

    /* Header */
    .hub-header {
        border-bottom: 2px solid var(--text-color);
        margin-bottom: 0.5rem;
        # background-color: #0a0;
    }
    .hub-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--text-color);
        letter-spacing: -0.02em;
    }
    .hub-subtitle {
        font-size: 0.9rem;
        color: var(--text-color);
        opacity: 0.6;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Login — credentials stored in .streamlit/secrets.toml
# ---------------------------------------------------------------------------

def check_login():
    """Show login form and return True if authenticated."""

    # User already authenticated
    if st.session_state.get("authenticated"):

        # Restore sidebar after login
        st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: block;
        }
        </style>
        """, unsafe_allow_html=True)

        return True

    # Hide sidebar before login
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-wrapper">
        <div class="login-title">⚡ Casco Energy Group</div>
        <div class="login-subtitle">Sign in to continue</div>
    </div>
    """, unsafe_allow_html=True)

    # Center the form using columns
    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        username = st.text_input("Username", placeholder="username")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        login_btn = st.button("Sign in", type="primary", use_container_width=True)

        if login_btn:
            valid_user = st.secrets["LOGIN_USERNAME"]
            valid_pass = st.secrets["LOGIN_PASSWORD"]

            if username == valid_user and password == valid_pass:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")

    return False


if not check_login():
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar logout button
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("<br>" * 8, unsafe_allow_html=True)
    if st.button("🚪 Sign out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hub-header">
    <div class="hub-title">⚡ Casco Energy Group</div>
    <div class="hub-subtitle">Select an application from the sidebar or the cards below</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# App cards
# — To add a new app: add a new entry to this list and create its page file
# ---------------------------------------------------------------------------

APPS = [
    {
        "icon": "📊",
        "title": "SIR Inventory",
        "description": "Downloads and consolidates the 6 NY DPS SIR Inventory files into a single CSV, ready for analysis.",
        "tag": "Data / Scraping",
        "page": "pages/SIR_Inventory.py",
    },
    {
        "icon": "📄",
        "title": "LOI Generator",
        "description": "Upload a template and generate a filled Letter of Intent document automatically.",
        "tag": "Document Generation",
        "page": "pages/LOI_Generator.py",
    },
    # -----------------------------------------------------------------------
    # ADD NEW APPS HERE — copy the dict above and fill in the details
    # -----------------------------------------------------------------------
]

# Render cards in columns (3 per row)
cols_per_row = 3
for i in range(0, len(APPS), cols_per_row):
    cols = st.columns(cols_per_row, gap="medium")
    for j, app in enumerate(APPS[i:i + cols_per_row]):
        with cols[j]:
            st.markdown(f"""
            <div class="app-card">
                <div class="icon">{app['icon']}</div>
                <h3>{app['title']}</h3>
                <p>{app['description']}</p>
                <span class="tag">{app['tag']}</span>
            </div>
            """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

# st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-family: IBM Plex Mono, monospace; font-size: 0.7rem; "
    "color: var(--text-color); opacity: 0.4; text-align: center;'>"
    "Casco Energy Group © 2026 — Built with Streamlit"
    "</p>",
    unsafe_allow_html=True
)
