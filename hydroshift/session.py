from datetime import datetime

import streamlit as st

from hydroshift.rserver.start_r_server import start_server


def init_session_state():
    """Initialize session state."""
    st.session_state["session_id"] = datetime.now()
    st.session_state["server"] = start_server()
    st.session_state["gage_id"] = None
