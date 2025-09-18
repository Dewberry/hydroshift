from datetime import date
import datetime
import time

import folium
import streamlit as st
from streamlit_folium import st_folium

from hydroshift.errors import GageNotFoundException
from hydroshift.utils.data_retrieval import Gage
from hydroshift.utils.ffa import LP3Analysis
from hydroshift.utils.jinja import write_template
from hydroshift.utils.plots import (
    plot_ams,
    plot_ams_seasonal,
    plot_daily_mean,
    plot_flow_stats,
    plot_lp3,
    plot_monthly_mean,
)


def section_ams(gage: Gage):
    """Display the AMS section."""
    if gage.ams is not None:
        if gage.missing_dates_ams is not None and len(gage.missing_dates_ams) > 0:
            st.warning(f"Missing {len(gage.missing_dates_ams)} AMS records")
        st.plotly_chart(plot_ams(gage.ams, gage.gage_id))
        show_data = st.checkbox("Show AMS Data Table")
        if show_data:
            st.dataframe(gage.ams)


def section_flow_stats(gage: Gage):
    """Display the flow statistics section."""
    if gage.flow_stats is not None:
        st.plotly_chart(plot_flow_stats(gage.flow_stats, gage.gage_id))
        show_data = st.checkbox("Show Daily Stats Data Table")
        if show_data:
            st.dataframe(gage.flow_stats)


def section_lp3(gage: Gage):
    """Display the FFA section."""
    if gage.ams is not None:
        # Options
        opt_col_1, opt_col_2 = st.columns(2)
        with opt_col_1:
            est_method = st.selectbox(
                "Estimation Method",
                ["L-moments", "Method of moments", "Maximum Likelihood"],
                index=1,
            )
            est_method = {
                "L-moments": "LMOM",
                "Method of moments": "MOM",
                "Maximum Likelihood": "MLE",
            }[est_method]
        with opt_col_2:
            with st.container():
                use_map = st.toggle("Use regional skew", value=False, disabled=not gage.has_regional_skew)
                lp3 = LP3Analysis(gage.gage_id, gage.ams_vals, use_map, est_method, "")
                st.badge(f"Using skew value of {round(lp3.parameters[2], 2)}", color="blue")

        # Analysis and display
        if gage.missing_dates_ams is not None and len(gage.missing_dates_ams) > 0:
            st.warning(f"Missing {len(gage.missing_dates_ams)} LP3 records")
        st.plotly_chart(plot_lp3(lp3), use_container_width=True)
        show_data = st.checkbox("Show LP3 Data Table")
        if show_data:
            st.dataframe(lp3.quantile_df)


def section_ams_seasonal(gage: Gage):
    """Display the ams with seasonal attributes section."""
    if gage.ams is not None:
        if gage.missing_dates_ams:
            st.warning(f"Missing {len(gage.missing_dates_ams)} AMS seasonal records")
        st.plotly_chart(plot_ams_seasonal(gage.ams, gage.gage_id), use_container_width=True)
        show_data = st.checkbox("Show Ranked Seasonal Data Table")
        if show_data:
            st.dataframe(gage.ams)


def section_daily_mean(gage: Gage):
    """Display the daily mean discharge section."""
    plot_col, input_col = st.columns([8, 2])

    with input_col:
        st.write("")  # blank line for more space
        st.write("Daily Mean Input Dates")
        start_date = datetime.date(1900, 1, 1)
        end_date = datetime.date(2100, 12, 31)
        start_date = st.date_input("Start Date", value=date(2024, 1, 1), min_value=start_date, max_value=end_date)
        end_date = st.date_input("End Date", value=date(2024, 12, 31), min_value=start_date, max_value=end_date)

    data = gage.get_daily_values(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )
    missing_dates = gage.missing_dates_daily_values(start_date, end_date)
    with plot_col:
        if data is not None:
            if missing_dates:
                st.warning(f"Missing {len(missing_dates)} daily mean records")
            if len(data) > 0:
                st.plotly_chart(plot_daily_mean(data, gage.gage_id), use_container_width=True)
                show_data = st.checkbox("Show Daily Mean Data Table")
                if show_data:
                    st.dataframe(data)
            else:
                st.warning("No data found for selected date range.")
        else:
            st.error(f"Could not find daily mean data for period {start_date} - {end_date}")


def section_monthly_mean(gage: Gage):
    """Display the monthly mean discharge section."""
    data = gage.monthly_values
    missing_dates = gage.missing_dates_monthly_values
    if data is not None and "mean_va" in data.columns:
        if missing_dates:
            st.warning(f"Missing {len(missing_dates)} monthly records")
        st.plotly_chart(
            plot_monthly_mean(data, st.session_state["gage_id"]),
            use_container_width=True,
        )

        show_data = st.checkbox("Show Monthly Mean Data Table")
        if show_data:
            st.dataframe(data)


SECTION_DICT = {
    "Daily Flow Statistics": section_flow_stats,
    "Annual Peak Flow (AMS)": section_ams,
    "Log-Pearson III (LP3) Analysis": section_lp3,
    "AMS Seasonal Ranking": section_ams_seasonal,
    "Daily Mean Streamflow": section_daily_mean,
    "Monthly Mean Streamflow": section_monthly_mean
}



def summary():
    """Display summary plots for various timeseries associated with this gage."""
    st.set_page_config(page_title="Gage Summary", layout="wide", initial_sidebar_state ="auto")

    # Sidebar for input
    with st.sidebar:
        # Gage select
        try:
            st.session_state["gage_id"] = st.text_input("Enter USGS Gage Number:", st.session_state["gage_id"])
            gage = Gage(st.session_state["gage_id"])
        except GageNotFoundException:
            gage = None

        # Footer
        st.divider()
        write_template("data_sources_side_bar.html")

    if gage is not None:
        if gage.latitude and gage.longitude:
            with st.container(border=True):
                info_col, map_col = st.columns(2)
                with map_col:  # Site map
                    mini_map = folium.Map(
                        location=[gage.latitude, gage.longitude],
                        zoom_start=7,
                        width=450,
                        height=200,
                    )
                    folium.Marker(
                        [gage.latitude, gage.longitude],
                        popup=f"Gage {st.session_state['gage_id']}",
                        icon=folium.Icon(color="green"),
                    ).add_to(mini_map)
                    st_folium(mini_map, use_container_width=True, height=250)
                with info_col:
                    # Display site metadata
                    st.subheader("Site Information")
                    write_template("site_summary.md", gage.site_data)
                    st.link_button("Go to USGS", f'https://waterdata.usgs.gov/monitoring-location/USGS-{st.session_state["gage_id"]}/')

        with st.spinner():
            gage.raise_warnings()
            if len(gage.available_plots) > 0:
                tabs = st.tabs(gage.available_plots)
                for t, i in zip(tabs, gage.available_plots):
                    with t:
                        SECTION_DICT[i](gage)
    else:
        st.error("USGS gage not found.")
