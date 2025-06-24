from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium

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
            st_skew = st.toggle("Use regional skew", value=False, disabled=not gage.has_regional_skew)
            if st_skew:
                use_map = True
            else:
                use_map = False

        # Analysis and display
        lp3 = LP3Analysis(gage.gage_id, gage.ams_vals, use_map, est_method, "")
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
        start_date = st.date_input("Start Date", value=date(2024, 1, 1))
        end_date = st.date_input("End Date", value=date(2024, 12, 31))

    data = gage.get_daily_values(
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d"),
    )
    missing_dates = gage.missing_dates_daily_values(start_date, end_date)
    with plot_col:
        if data is not None:
            if missing_dates:
                st.warning(f"Missing {len(missing_dates)} daily mean records")
            st.plotly_chart(plot_daily_mean(data, gage.gage_id), use_container_width=True)
            show_data = st.checkbox("Show Daily Mean Data Table")
            if show_data:
                st.dataframe(data)


def section_monthly_mean(gage: Gage):
    """Display the monthly mean discharge section."""
    data = gage.get_monthly_values()
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
        with st.spinner("Loading gage data..."):  # This is here to clear previous pages while data loads.
            pass

        col2, col3 = st.columns([6, 2], gap="large")

        if gage.latitude and gage.longitude:
            with col3:  # Site map
                st.subheader("Gage Location")

                # Create Folium Map
                mini_map = folium.Map(
                    location=[gage.latitude, gage.longitude],
                    zoom_start=7,
                    width=200,
                    height=200,
                )
                folium.Marker(
                    [gage.latitude, gage.longitude],
                    popup=f"Gage {st.session_state['gage_id']}",
                    icon=folium.Icon(color="green"),
                ).add_to(mini_map)
                st_folium(mini_map, width=250, height=250)

                # Display site metadata
                st.subheader("Site Information")
                write_template("site_summary.md", gage.site_data)

        with col2:  # Center column for plots
            gage.raise_warnings()
            if show_ams:
                section_ams(gage)
            if show_daily_stats:
                section_flow_stats(gage)
            if show_lp3:
                section_lp3(gage)
            if show_ams_seasonal:
                section_ams_seasonal(gage)
            if show_daily_mean:
                section_daily_mean(gage)
            if show_monthly_mean:
                section_monthly_mean(gage)
