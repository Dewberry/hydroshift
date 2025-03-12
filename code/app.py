import streamlit as st
import folium
from streamlit_folium import st_folium
from plots import plot_ams, plot_flow_stats, plot_lp3, plot_ams_seasonal, plot_daily_mean, plot_monthly_mean
from data_retrieval import get_ams, get_flow_stats, load_site_data, get_daily_values, get_monthly_values

st.set_page_config(page_title="USGS Gage Data Viewer", layout="wide")

st.session_state["gage_id"] = "12105900"
# Sidebar for input
with st.sidebar:
    st.title("Settings")
    st.session_state["gage_id"] = st.text_input("Enter USGS Gage Number:", st.session_state["gage_id"])
    plot_type = st.selectbox(
        "Select Data to Plot:",
        [
            "Annual Peak Flow (AMS)",
            "Daily Flow Statistics",
            "Log-Pearson III (LP3) Analysis",
            "AMS Seasonal Ranking",
            "Daily Mean Streamflow",
            "Monthly Mean Streamflow",
        ],
    )

if st.session_state["gage_id"]:
    try:
        site_data = load_site_data(st.session_state["gage_id"])
        lat, lon = site_data["Latitude"], site_data["Longitude"]
    except ValueError as e:
        lat, lon = None, None
        st.error(f"{e}")

    col1, col2, col3 = st.columns([1, 6, 2])

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
            st.markdown(
                f"""
            **Site Number:** {site_data["Site Number"]} <br>
            **Station Name:** {site_data["Station Name"]} <br>
            **Latitude:** {site_data["Latitude"]} <br>
            **Longitude:** {site_data["Longitude"]} <br>
            **Drainage Area:** {site_data["Drainage Area"]} <br>
            **HUC Code:** {site_data["HUC Code"]} <br>
            **Elevation Datum:** {site_data["Elevation Datum"]}
            """,
                unsafe_allow_html=True,
            )

    with col2:  # Center column
        if plot_type == "Annual Peak Flow (AMS)":
            data, missing_years = get_ams(st.session_state["gage_id"])
            if data is not None and "peak_va" in data.columns:
                if missing_years:
                    st.warning(f"Missing {len(missing_years)} dates between {data.index.min()} and {data.index.max()}")
                st.plotly_chart(plot_ams(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No peak flow data available.")

        elif plot_type == "Daily Flow Statistics":
            data = get_flow_stats(st.session_state["gage_id"])
            if data is not None and "mean_va" in data.columns:
                st.plotly_chart(plot_flow_stats(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No flow statistics available.")

        elif plot_type == "Log-Pearson III (LP3) Analysis":
            data, missing_years = get_ams(st.session_state["gage_id"], True)
            if data is not None:
                if missing_years:
                    st.warning(f"Missing {len(missing_years)} dates between {data.index.min()} and {data.index.max()}")
                st.plotly_chart(plot_lp3(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No LP3 data available.")

        elif plot_type == "AMS Seasonal Ranking":
            data, missing_years = get_ams(st.session_state["gage_id"])
            if data is not None and "peak_va" in data.columns:
                if missing_years:
                    st.warning(f"Missing {len(missing_years)} dates between {data.index.min()} and {data.index.max()}")
                st.plotly_chart(plot_ams_seasonal(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No AMS seasonal data available.")

        elif plot_type == "Daily Mean Streamflow":
            start_date = st.sidebar.text_input("Enter Start Date (YYYY-MM-DD)", "2024-01-01")
            end_date = st.sidebar.text_input("Enter End Date (YYYY-MM-DD)", "2024-12-31")

            data, missing_dates = get_daily_values(st.session_state["gage_id"], start_date, end_date)

            if data is not None:
                if missing_dates:
                    st.warning(f"Missing {len(missing_dates)} dates between {data.index.min()} and {data.index.max()}")
                st.plotly_chart(plot_daily_mean(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No daily mean data available for this period.")

        elif plot_type == "Monthly Mean Streamflow":
            data, missing_dates = get_monthly_values(st.session_state["gage_id"])
            if data is not None and "mean_va" in data.columns:
                if missing_dates:
                    st.warning(
                        f"Missing {len(missing_dates)} dates between {data['date'].min()} and {data['date'].max()}"
                    )
                st.plotly_chart(plot_monthly_mean(data, st.session_state["gage_id"]), use_container_width=True)
            else:
                st.error("No daily mean data available for this period.")
        if data is not None:
            st.dataframe(data)
