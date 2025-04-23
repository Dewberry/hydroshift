import pandas as pd
import streamlit as st

from hydroshift.data_retrieval import (
    check_missing_dates,
    get_ams,
    get_daily_values,
    get_flow_stats,
    get_monthly_values,
    load_site_data,
)


class Gage:
    """A USGS Gage."""

    def __init__(self, gage_id: str):
        """Construct class."""
        self.gage_id = gage_id
        self.site_data = load_site_data(gage_id)

    @property
    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def latitude(self) -> float:
        """Latitude of gage."""
        return self.site_data.get("dec_lat_va")

    @property
    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def longitude(self) -> float:
        """Longitude of gage."""
        return self.site_data.get("dec_long_va")

    @property
    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def ams(self) -> pd.DataFrame:
        """Load AMS for this site."""
        return get_ams(self.gage_id)

    @property
    def missing_dates_ams(self) -> list:
        """Get missing dates for AMS."""
        return check_missing_dates(self.ams, "water_year")

    @property
    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def flow_stats(self) -> pd.DataFrame:
        """Load flow statistics for this site."""
        return get_flow_stats(self.gage_id)

    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def get_daily_values(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load daily mean discharge for this site."""
        return get_daily_values(self.gage_id, start_date, end_date)

    @property
    def missing_dates_daily_values(self, start_date: str, end_date: str) -> list:
        """Get missing dates for mean daily value series."""
        return check_missing_dates(self.get_daily_values(start_date, end_date), "daily")

    @st.cache_data(hash_funcs={"__main__.Gage": lambda x: hash(x.gage_id)})
    def get_monthly_values(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load monthly mean discharge for this site."""
        return get_monthly_values(self.gage_id, start_date, end_date)

    @property
    def missing_dates_monthly_values(self, start_date: str, end_date: str) -> list:
        """Get missing dates for mean monthly value series."""
        return check_missing_dates(self.get_monthly_values(start_date, end_date), "monthly")
