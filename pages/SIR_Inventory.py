"""
SIR Inventory — Streamlit Page
================================
Runs the scraper and lets the user download the consolidated CSV.
"""

import io
import logging
import streamlit as st
from datetime import datetime
from pathlib import Path
from auth import require_auth

require_auth()

# Import core logic from the scraper module
# Make sure sir_download_combine.py is in the same directory as app.py
import sys
sys.path.append(str(Path(__file__).parent.parent))
from sir_download_combine import (
    download_files,
    read_and_map,
    DOWNLOAD_URLS,
    get_utility_name,
)
import pandas as pd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="SIR Inventory — Casco Energy",
    page_icon="📊",
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
    .status-box {
        background: #fff;
        border: 1px solid #e0ddd5;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1.5rem;
    }
    .utility-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #f0ede6;
        font-size: 0.875rem;
    }
    .utility-row:last-child { border-bottom: none; }
    .badge {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
    }
    .badge-error {
        background: #fce4ec;
        color: #c62828;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------

st.markdown('<div class="page-title">📊 SIR Inventory Consolidator</div>', unsafe_allow_html=True)

st.markdown(
    "Downloads the 6 SIR Inventory files from the **NY DPS website**, "
    "consolidates them into a single CSV, and makes it available for download."
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Run button
# ---------------------------------------------------------------------------

col1, col2 = st.columns([1, 3])

with col1:
    run = st.button("▶ Run Scraper", type="primary", use_container_width=True)

with col2:
    st.caption(f"Source: [NY DPS — Distributed Generation Information](https://dps.ny.gov/distributed-generation-information)")

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

if run:
    temp_dir = Path("_sir_temp")
    raw_dir  = temp_dir / "raw"

    results  = []   # list of (utility_name, rows, status, error)
    dfs      = []

    # --- Download ---
    progress = st.progress(0, text="Starting download...")
    status   = st.empty()

    try:
        raw_files = download_files(raw_dir)
    except Exception as e:
        st.error(f"Download failed: {e}")
        st.stop()

    # --- Read & map each file ---
    total = len(raw_files)
    for i, path in enumerate(raw_files):
        utility_name = get_utility_name(path)
        progress.progress((i + 1) / (total * 2), text=f"Processing: {utility_name}...")
        status.caption(f"Reading {path.name}...")

        try:
            df = read_and_map(path, utility_name)
            dfs.append(df)
            results.append((utility_name, len(df), "ok", None))
        except Exception as e:
            results.append((utility_name, 0, "error", str(e)))

    # --- Combine ---
    if not dfs:
        st.error("No files could be processed.")
        st.stop()

    progress.progress(0.95, text="Combining files...")
    status.caption("Writing CSV...")

    combined  = pd.concat(dfs, ignore_index=True, sort=False)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename  = f"SIR_Inventory_Combined_{timestamp}.csv"

    csv_buffer = io.StringIO()
    combined.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    progress.progress(1.0, text="Done!")
    status.empty()

    # --- Summary ---
    st.success(f"✅ Consolidation complete — **{len(combined):,} rows** across **{len(dfs)} utilities**")

    st.markdown('<div class="status-box">', unsafe_allow_html=True)
    st.markdown("**Files processed:**")
    for (name, rows, status_val, error) in results:
        badge = f'<span class="badge">{rows:,} rows</span>' if status_val == "ok" \
                else f'<span class="badge badge-error">Error: {error}</span>'
        st.markdown(
            f'<div class="utility-row"><span>{name}</span>{badge}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # --- Download button ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="⬇ Download CSV",
        data=csv_bytes,
        file_name=filename,
        mime="text/csv",
        type="primary",
        use_container_width=False,
    )

    # --- Cleanup temp files ---
    try:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass
