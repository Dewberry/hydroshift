import logging
import sys
import time
import streamlit as st
from session import init_session_state
from PIL import Image

from hydroshift._pages import changepoint, homepage, summary, reset_homepage

from hydroshift.logging import  setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def navigator():
    """Make sidebar for multi-page navigation."""
    time.sleep(0.1)
    # Define general style
    im = Image.open("hydroshift/images/favicon.ico")
    st.set_page_config(page_title="HydroShift",page_icon=im)

    # Initialize state
    if "session_id" not in st.session_state:
        init_session_state()

    # Define pages
    changepoint_pg = st.Page(changepoint, title="Changepoint Analysis")
    summary_pg = st.Page(summary, title="Gage Summary")
    home = st.Page(homepage, title="Homepage")
    reset_home = st.Page(reset_homepage, title="Homepage")

    # Setup sidebar
    if st.session_state["gage_id"] is not None:
        summary_pg._default = True
        nav = st.navigation([reset_home, summary_pg, changepoint_pg], position="sidebar")
    else:
        home._default = True
        nav = st.navigation([home], position="hidden")
    nav.run()


if __name__ == "__main__":
    navigator()
