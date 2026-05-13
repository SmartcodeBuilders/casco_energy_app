import streamlit as st

def excel_upload_section():
    excel_file = st.file_uploader("Upload your Excel file ⬆️", type=["xlsx", "xls"])
    first_row = st.number_input("First row with data", min_value=1, value=5)
    tag_col = st.number_input("Tag column", min_value=1, value=6)
    user_input_col = st.number_input("User Input column", min_value=1, value=5)
    return excel_file, first_row, tag_col, user_input_col

def word_upload_section():
    return st.file_uploader("Select Template to Update (.docx) ⬆️", type=["docx"])

def preview_dataframe(df):
    if df is not None:
        st.subheader("Preview of Extracted Data Pair: Tag - Information")
        st.dataframe(df)
