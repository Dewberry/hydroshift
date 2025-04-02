import folium
import streamlit as st
from streamlit_folium import st_folium
from hydroshift.pages.Change_Point import main
from data_retrieval import load_site_data

from session import init_session_state



def app():
    st.set_page_config(page_title="HydroShift", layout="wide")

    if "session_id" not in st.session_state:
        init_session_state()

    # CSS to remove sidebar from landing page
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
            try:
                st.session_state["site_data"] = load_site_data(st.session_state["gage_id"])
                st.switch_page('pages/Gage_Summary.py')
            except ValueError as e:
                st.error(f"Data not found for gage: {st.session_state['gage_id']}")
        if demo:
            st.session_state["gage_id"] = st.session_state["sample_gage"]
            st.session_state["site_data"] = load_site_data(st.session_state["gage_id"])
            st.switch_page('pages/Gage_Summary.py')
    with right_col:
        st.image("/workspaces/non-stationarity-tool/hydroshift/images/conus_usgs_map.png")

if __name__=="__main__":
    app()