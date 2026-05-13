import streamlit as st
import re
from datetime import date, timedelta, time

def format_for_document(value, currency=False):
    """
    Format a number for the final document:
    - Currency: $ + thousand separator, 2 decimals if needed
    - Non-currency: just thousand separator
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return str(value)  # fallback if not a number

    if currency:
        return f"${int(val):,}" if val.is_integer() else f"${val:,.2f}"
    else:
        return f"{int(val):,}" if val.is_integer() else f"{val:,.2f}"


def formatted_number_input(
    label: str,
    key: str,
    default="",
    currency: bool = False
):
    error_key = f"{key}_error"

    def format_value():
        try:
            raw = st.session_state[key]

            # Strip symbols
            raw_clean = raw.replace("$", "").replace(",", "")

            # Validate numeric pattern
            if not re.fullmatch(r"\d*\.?\d*", raw_clean):
                st.session_state[error_key] = True
                return
            else:
                st.session_state[error_key] = False

            if raw_clean == "":
                return  # keep blank

            val = float(raw_clean)

            if currency:
                st.session_state[key] = (
                    f"${int(val):,}" if val.is_integer()
                    else f"${val:,.2f}"
                )
            else:
                st.session_state[key] = (
                    f"{int(val):,}" if val.is_integer()
                    else f"{val:,.2f}"
                )

        except Exception:
            st.session_state[error_key] = True

    # Initialize value
    if key not in st.session_state:
        st.session_state[key] = "" if default in ("", None) else (
            f"${float(default):,.2f}" if currency else f"{float(default):,.2f}"
        )
        st.session_state[error_key] = False

    user_input = st.text_input(
        label=label,
        key=key,
        on_change=format_value
    )

    # Show visual error feedback
    if st.session_state.get(error_key):
        st.markdown("<span style='color:red;'>Please enter a valid number.</span>", unsafe_allow_html=True)

    # Return parsed value or empty
    cleaned = user_input.replace("$", "").replace(",", "")
    if cleaned == "" or st.session_state.get(error_key):
        return ""
    return float(cleaned)



def render_dynamic_form(fields: list) -> dict:
    """
    Render a dynamic Streamlit form from a field configuration list.

    Field config example:
    {
        "name": "LEASE_RENT",
        "label": "Lease Payment Amount",
        "type": "number",
        "currency": True
    }
    """
    context = {}

    for field in fields:
        field_name = field["name"]
        field_label = field.get("label", field_name)
        field_type = field.get("type", "text")
        is_currency = field.get("currency", False)
        default = field.get("default", "")

        if field_type == "text":
            context[field_name] = st.text_input(
                label=field_label,
                value=default,
                key=field_name
            )

        elif field_type == "number":
            context[field_name] = formatted_number_input(
                label=field_label,
                key=field_name,
                # default=default or 0,
                default=default,
                currency=is_currency
            )

        elif field_type == "date":
            d = st.date_input(
                label=field_label,
                value=default or date.today(),
                key=field_name
            )
            context[field_name] = d.strftime("%B %d, %Y")
        elif field_type == "label_only":
            st.markdown(f"### {field_label}")
            context[field_name] = None
        elif field_type == "period":
            start_default = field.get("start_default")
            end_offset = field.get("end_offset_days", 0)

            # Resolve start date
            if isinstance(start_default, str):
                start_date = st.session_state.get(start_default, date.today())
            else:
                start_date = date.today()

            end_date = start_date + timedelta(days=end_offset)

            # Render date range picker
            period_value = st.date_input(
                label=field_label,
                value=(start_date, end_date),
                key=field_name
            )

            # Show placeholder until both dates are selected
            if isinstance(period_value, tuple) and len(period_value) == 2:
                start, end = period_value
                context[field_name] = f"{start.strftime('%b %d, %Y')} to {end.strftime('%b %d, %Y')}"
            else:
                # Placeholder text (or you can use "")
                context[field_name] = "Select both start and end dates"
        elif field_type == "hourly_period":
            cols = st.columns(2)

            with cols[0]:
                start = st.time_input(f"{field_label} Start", key=f"{field_name}_start")

            with cols[1]:
                end = st.time_input(f"{field_label} End", key=f"{field_name}_end")

            context[field_name] = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

        else:
            context[field_name] = st.text_input(
                label=field_label,
                value=default,
                key=field_name
            )

    return context
