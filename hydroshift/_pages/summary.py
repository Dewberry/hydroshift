import folium
import streamlit as st
from data_retrieval import (
    get_ams,
    get_daily_values,
    get_flow_stats,
    get_monthly_values,
)
from plots import (
    plot_ams,
    plot_ams_seasonal,
    plot_daily_mean,
    plot_flow_stats,
    plot_lp3,
    plot_monthly_mean,
)
from streamlit_folium import st_folium

from hydroshift.utils.data_models import Gage
from hydroshift.utils.jinja import write_template


def summary():
    """Display summary plots for various timeseries associated with this gage."""
    st.set_page_config(page_title="Gage Summary", layout="wide")
    # Sidebar for input
    with st.sidebar:
        st.title("Settings")
        st.session_state["gage_id"] = st.text_input("Enter USGS Gage Number:", st.session_state["gage_id"])
        gage = Gage(st.session_state["gage_id"])

        # Toggle plots
        st.markdown("### Toggle Plots")
        show_ams = st.checkbox("Annual Peak Flow (AMS)", value=True)
        show_daily_stats = st.checkbox("Daily Flow Statistics", value=True)
        show_lp3 = st.checkbox("Log-Pearson III (LP3) Analysis", value=True)
        show_ams_seasonal = st.checkbox("AMS Seasonal Ranking", value=True)
        show_daily_mean = st.checkbox("Daily Mean Streamflow", value=True)
        show_monthly_mean = st.checkbox("Monthly Mean Streamflow", value=True)

        # Data sources
        st.divider()
        write_template("data_sources_side_bar.html")

    if st.session_state["gage_id"]:
        with st.spinner("Loading gage data..."):  # This is mainly here to clear previous pages while data loads.
            try:
                if st.session_state["gage_id"] == "testing":
                    site_data = {
                        "site_no": "-99999",
                        "station_nm": "Wet River",
                        "dec_lat_va": 45,
                        "dec_long_va": -103,
                        "drain_area_va": 0,
                        "huc_cd": 0,
                        "alt_datum_cd": "NAVD88",
                    }
                else:
                    site_data = st.session_state["site_data"]
                lat, lon = site_data["dec_lat_va"], site_data["dec_long_va"]
            except ValueError as e:
                lat, lon = None, None
                st.error(f"{e}")

        col2, col3 = st.columns([6, 2], gap="large")

        if lat and lon:
            with col3:
                st.subheader("Gage Location")

                # Create Folium Map
                mini_map = folium.Map(location=[lat, lon], zoom_start=7, width=200, height=200)
                folium.Marker(
                    [lat, lon], popup=f"Gage {st.session_state['gage_id']}", icon=folium.Icon(color="green")
                ).add_to(mini_map)
                st_folium(mini_map, width=250, height=250)

                # Display site metadata
                st.subheader("Site Information")
                write_template("site_summary.md", site_data)

        with col2:  # Center column for plots
            if show_ams:
                ams = get_ams(st.session_state["gage_id"])
                data, missing_years = ams["peaks"], ams["missing_years"]
                if data is not None and "peak_va" in data.columns:
                    if missing_years:
                        st.warning(f"Missing {len(missing_years)} AMS records")
                    st.plotly_chart(plot_ams(data, st.session_state["gage_id"]), use_container_width=True)
                    show_data = st.checkbox("Show AMS Data Table")
                    if show_data:
                        st.dataframe(data)

            if show_daily_stats:
                data = get_flow_stats(st.session_state["gage_id"])
                if data is not None and "mean_va" in data.columns:
                    st.plotly_chart(plot_flow_stats(data, st.session_state["gage_id"]), use_container_width=True)
                    show_data = st.checkbox("Show Daily Stats Data Table")
                    if show_data:
                        st.dataframe(data)

            if show_lp3:
                ams = get_ams(st.session_state["gage_id"])
                if ams["peaks"] is not None:
                    if ams["missing_years"]:
                        st.warning(f"Missing {len(ams["missing_years"])} LP3 records")
                    st.plotly_chart(plot_lp3(ams, st.session_state["gage_id"]), use_container_width=True)
                    show_data = st.checkbox("Show LP3 Data Table")
                    if show_data:
                        st.dataframe(ams["lp3"])
            if show_ams_seasonal:
                ams = get_ams(st.session_state["gage_id"])
                data, missing_years = ams["peaks"], ams["missing_years"]
                if data is not None and "peak_va" in data.columns:
                    if missing_years:
                        st.warning(f"Missing {len(missing_years)} AMS seasonal records")
                    st.plotly_chart(plot_ams_seasonal(data, st.session_state["gage_id"]), use_container_width=True)
                    show_data = st.checkbox("Show Ranked Seasonal Data Table")
                    if show_data:
                        st.dataframe(data)

            if show_daily_mean:
                plot_col, input_col = st.columns([8, 2])

                with input_col:
                    st.write("")  # blank line for more space
                    st.write("Daily Mean Input Dates")
                    start_date = st.text_input("Start Date (YYYY-MM-DD)", "2024-01-01")
                    end_date = st.text_input("End Date (YYYY-MM-DD)", "2024-12-31")

                data, missing_dates = get_daily_values(st.session_state["gage_id"], start_date, end_date)
                with plot_col:
                    if data is not None:
                        if missing_dates:
                            st.warning(f"Missing {len(missing_dates)} daily mean records")
                        st.plotly_chart(plot_daily_mean(data, st.session_state["gage_id"]), use_container_width=True)
                        show_data = st.checkbox("Show Daily Mean Data Table")
                        if show_data:
                            st.dataframe(data)

            if show_monthly_mean:
                data, missing_dates = get_monthly_values(st.session_state["gage_id"])
                if data is not None and "mean_va" in data.columns:
                    if missing_dates:
                        st.warning(f"Missing {len(missing_dates)} monthly records")
                    st.plotly_chart(plot_monthly_mean(data, st.session_state["gage_id"]), use_container_width=True)

                    show_data = st.checkbox("Show Monthly Mean Data Table")
                    if show_data:
                        st.dataframe(data)
