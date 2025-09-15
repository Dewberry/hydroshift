import streamlit as st
from session import init_session_state
from PIL import Image

from hydroshift._pages import changepoint, homepage, summary


def navigator():
    """Make sidebar for multi-page navigation."""
    # Define general style
    im = Image.open("hydroshift/images/favicon.ico")
    st.set_page_config(
        page_title="HydroShift",
        page_icon=im,
    )

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
