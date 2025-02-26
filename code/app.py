import streamlit as st
import folium
from streamlit_folium import st_folium
from plots import plot_ams, plot_flow_stats, plot_lp3, plot_ams_seasonal, plot_daily_mean, plot_monthly_mean
from data_retrieval import get_ams, get_flow_stats, load_site_data, get_daily_values, get_monthly_values

st.set_page_config(page_title="USGS Gage Data Viewer", layout="wide")

# Sidebar for input
with st.sidebar:
    st.title("Settings")
    gage_id = st.text_input("Enter USGS Gage Number:", "12105900")
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

if gage_id:
    site_data = load_site_data(gage_id)
    if site_data:
        lat, lon = site_data["Latitude"], site_data["Longitude"]
    else:
        lat, lon = None, None

    col1, col2, col3 = st.columns([1, 6, 2])

    if lat and lon:
        with col3:
            st.subheader("Gage Location")

            # Create Folium Map
            mini_map = folium.Map(location=[lat, lon], zoom_start=7, width=200, height=200)
            folium.Marker([lat, lon], popup=f"Gage {gage_id}", icon=folium.Icon(color="green")).add_to(mini_map)
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
    else:
        st.error("No site information available.")

    with col2:  # Center column
        if plot_type == "Annual Peak Flow (AMS)":
            data = get_ams(gage_id)
            if data is not None and "peak_va" in data.columns:
                st.plotly_chart(plot_ams(data, gage_id), use_container_width=True)
            else:
                st.error("No peak flow data available.")

        elif plot_type == "Daily Flow Statistics":
            data = get_flow_stats(gage_id)
            if data is not None and "mean_va" in data.columns:
                st.plotly_chart(plot_flow_stats(data, gage_id), use_container_width=True)
            else:
                st.error("No flow statistics available.")

        elif plot_type == "Log-Pearson III (LP3) Analysis":
            data = get_ams(gage_id, True)
            if data is not None:
                st.plotly_chart(plot_lp3(data, gage_id), use_container_width=True)
            else:
                st.error("No LP3 data available.")

        elif plot_type == "AMS Seasonal Ranking":
            data = get_ams(gage_id)
            if data is not None and "peak_va" in data.columns:
                st.plotly_chart(plot_ams_seasonal(data, gage_id), use_container_width=True)
            else:
                st.error("No AMS seasonal data available.")

        elif plot_type == "Daily Mean Streamflow":
            start_date = st.sidebar.text_input("Enter Start Date (YYYY-MM-DD)", "2024-01-01")
            end_date = st.sidebar.text_input("Enter End Date (YYYY-MM-DD)", "2024-12-31")

            data = get_daily_values(gage_id, start_date, end_date)

            if data is not None and "00060_Mean" in data.columns:
                st.plotly_chart(plot_daily_mean(data, gage_id), use_container_width=True)
            else:
                st.error("No daily mean data available for this period.")

        elif plot_type == "Monthly Mean Streamflow":
            data = get_monthly_values(gage_id)
            if data is not None and "mean_va" in data.columns:
                st.plotly_chart(plot_monthly_mean(data, gage_id), use_container_width=True)
            else:
                st.error("No daily mean data available for this period.")

        st.dataframe(data)
