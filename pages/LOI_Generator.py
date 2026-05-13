import streamlit as st

# ---------------------------------------------------------------------------
# Authentication check
# ---------------------------------------------------------------------------

if not st.session_state.get("authenticated"):
    st.warning("Please sign in from the main page.")
    st.stop()


st.set_page_config(
    page_title="LOI Automator",
    layout="centered"
)

import json
from utils.form_utils import render_dynamic_form
from utils.word_utils import process_word_template
from utils.ui_components import word_upload_section
from datetime import date
from pathlib import Path
from auth import require_auth

require_auth()

# -------------------------------
# Helper function for document formatting
# -------------------------------
def format_for_document(value, currency=False):
    """
    Format a number for the final document:
    - Currency: $ + thousand separator, always 2 decimals
    - Non-currency: thousand separator, always 2 decimals
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)  # fallback if not a number

    if currency:
        return f"${val:,.2f}"
    else:
        return f"{val:,.2f}"


# -------------------------------
# 0. Load field definitions
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
TAGS_PATH = BASE_DIR / "data" / "tags.json"

with open(TAGS_PATH, "r") as f:
    fields = json.load(f)

# -------------------------------
# 1. Page config
# -------------------------------
st.set_page_config(page_title="LOI Automator", layout="centered")
st.title("LOI Automator")

# -------------------------------
# 2. Initialize session state 
# -------------------------------
for key in ["context", "output"]:
    if key not in st.session_state:
        st.session_state[key] = {}

# -------------------------------
# 3. Upload Word template
# -------------------------------
st.header("1. Upload Template Document")
word_file = word_upload_section()

# -------------------------------
# 4. Fill out dynamic form
# -------------------------------
st.header("2. General Project Info")
context = render_dynamic_form(fields)
if context is not None:
    st.session_state["context"] = context

    # -------------------------------
    # 4a. Format numbers for document
    # -------------------------------
    formatted_doc = {}
    for field in fields:
        name = field["name"]
        is_currency = field.get("currency", False)
        value = context.get(name)

        if field["type"] == "number":
            formatted_doc[name] = format_for_document(value, currency=is_currency)
        else:
            formatted_doc[name] = value

# -------------------------------
# 5. Filename input
# -------------------------------
st.header("3. LOI File Name")
filename = st.text_input(
    "Enter file name for download:", value="processed.docx", key="download_filename"
)

# -------------------------------
# 6. Process Word button
# -------------------------------
if word_file and st.session_state.get("context"):
    if st.button("Generate PDP"):
        # Preserve empty tags in Word template
        context_fixed = {
            key: (f"{{{{{key}}}}}" if value in ["", None] else formatted_doc.get(key, value))
            for key, value in st.session_state["context"].items()
        }

        st.session_state["output"] = process_word_template(word_file, context_fixed)
        if st.session_state["output"]:
            st.success("✅ File processed successfully!")

# -------------------------------
# 7. Download button
# -------------------------------
if st.session_state.get("output"):
    st.download_button(
        label="⬇️ Download File",
        data=st.session_state["output"],
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
