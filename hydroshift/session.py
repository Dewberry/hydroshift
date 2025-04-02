import streamlit as st
from datetime import datetime
from hydroshift.rserver.start_r_server import start_server

DEMO_GAGE="12105900"

def init_session_state():
    """."""
    st.session_state["session_id"] = datetime.now()
    st.session_state["server"] = start_server()
    st.session_state["gage_id"] = None
    st.session_state["sample_gage"] = DEMO_GAGE