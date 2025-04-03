import streamlit as st
from data_retrieval import load_site_data
from session import init_session_state

from hydroshift._pages import changepoint, summary
from hydroshift.consts import DEFAULT_GAGE


def homepage():
    """Landing page for app."""
    st.set_page_config(page_title="HydroShift", layout="wide")

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.title("HydroShift")
        st.subheader("USGS Streamflow Change Detection Tool")
        st.markdown(
            """
        Hydroshift is a web app for exploring long-term trends in streamflow data from USGS gaging stations.
        This tool provides interactive plots of annual peak flows, seasonal patterns, daily and monthly trends,
        and changepoint analysis to detect shifts in hydrologic behavior.
        """
        )

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
            try:
                st.session_state["site_data"] = load_site_data(st.session_state["gage_id"])
            except ValueError:
                st.error(f"Data not found for gage: {st.session_state['gage_id']}")
            st.rerun()


def navigator():
    """Make sidebar for multi-page navigation."""
    # Initialize state
    if "session_id" not in st.session_state:
        init_session_state()

    # Define pages
    changepoint_pg = st.Page(changepoint, title="Changepoint Analysis")
    summary_pg = st.Page(summary, title="Gage Summary", default=True)
    home = st.Page(homepage, title="Homepage", default=True)

    # Setup sidebar
    if st.session_state["gage_id"] is not None:
        nav = st.navigation([summary_pg, changepoint_pg], position="sidebar")
    else:
        nav = st.navigation([home], position="hidden")
    nav.run()


if __name__ == "__main__":
    navigator()
