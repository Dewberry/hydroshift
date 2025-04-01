import folium
import streamlit as st
from streamlit_folium import st_folium

from hydroshift.pages.changepoint import main
from hydroshift.rserver.start_r_server import start_server

start_server()

st.set_page_config(page_title="HydroShift: USGS Gage Viewer", layout="wide")

# CSS too remove sidebar from landing page
hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)


left_col, right_col = st.columns([2, 1])

with left_col:
    st.title("HydroShift")
    st.subheader("USGS Streamflow Change Detection Tool")
    st.markdown(
    '''
    Hydroshift is a web app for exploring long-term trends in streamflow data from USGS gaging stations.
    This tool provides interactive plots of annual peak flows, seasonal patterns, daily and monthly trends,
    and changepoint analysis to detect shifts in hydrologic behavior.
    '''
    )

    st.write("") #blank line for more space
    gage_input = st.text_input("Enter a USGS Gage Number to begin:")
    col1, col2 = st.columns([1,8])
    with col1:
        submit = st.button("Submit")
    with col2:
        demo = st.button("Use Demo Data")

    if submit and gage_input:
        st.session_state["gage_id"] = gage_input
        st.switch_page('pages/summary_page.py')
    if demo:
        st.session_state["gage_id"] = "12105900"
        st.switch_page('pages/summary_page.py')
with right_col:
    st.image("/workspaces/non-stationarity-tool/hydroshift/conus_usgs_map.png")



# st.session_state["gage_id"] = "12105900"