import streamlit as st

from hydroshift.consts import DEFAULT_GAGE
from hydroshift.utils.jinja import write_template


def homepage():
    """Landing page for app."""
    st.set_page_config(page_title="HydroShift", layout="wide")

    left_col, right_col, _ = st.columns([2, 1.5, 0.2], gap="large")

    with left_col:
        st.title("HydroShift")
        st.subheader("USGS Streamflow Change Detection Tool")
        write_template("app_description.md")

        st.write("")  # blank line for more space
        gage_input = st.text_input("Enter a USGS Gage Number to begin:")
        col1, col2 = st.columns([1, 8])
        with col1:
            submit = st.button("Submit")
        with col2:
            demo = st.button("Use Demo Data")

        if submit and gage_input:
            st.session_state["gage_id"] = gage_input
        if demo:
            st.session_state["gage_id"] = DEFAULT_GAGE
        if st.session_state["gage_id"] is not None:
            # try:
            #     st.session_state["site_data"] = load_site_data(st.session_state["gage_id"])
            # except ValueError:
            #     st.error(f"Data not found for gage: {st.session_state['gage_id']}")
            st.rerun()
    with right_col:
        st.title("")
        st.image("hydroshift/images/logo_base.png")

    write_template("footer.html")
