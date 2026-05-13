from docxtpl import DocxTemplate
from jinja2 import Environment, Undefined
from io import BytesIO
import streamlit as st

# --- Custom Undefined class to keep placeholders exactly as-is ---
class KeepPlaceholderUndefined(Undefined):
    def __str__(self):
        if self._undefined_name is not None:
            return f"{{{{{self._undefined_name}}}}}"
        return ""

# --- Function to process Word template ---
def process_word_template(word_file, context):
    try:
        doc = DocxTemplate(word_file)

        # Create Jinja2 environment with our custom Undefined
        jinja_env = Environment(undefined=KeepPlaceholderUndefined)
        doc.render(context, jinja_env=jinja_env)

        # Save the processed file in memory
        output = BytesIO()
        doc.save(output)
        output.seek(0)
        return output

    except Exception as e:
        st.error(f"⚠️ Error processing Word template: {e}")
        return None
