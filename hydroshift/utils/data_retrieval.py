from functools import cached_property
import logging
import time
import traceback
from typing import List

import numpy as np
import pandas as pd
import rasterio
import requests
import streamlit as st
from dataretrieval import NoSitesError, nwis
from scipy.stats import genpareto

from hydroshift.consts import REGULATION_MAP, MAX_CACHE_ENTRIES
from hydroshift.utils.common import group_consecutive_years


class Gage:
    """A USGS Gage."""

    def __init__(self, gage_id: str):
        """Construct class."""
        self.gage_id = gage_id
        self.site_data = load_site_data(gage_id)
        self.data_catalog = get_site_catalog(gage_id)

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def latitude(self) -> float:
        """Latitude of gage."""
        return self.site_data.get("dec_lat_va")

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def longitude(self) -> float:
        """Longitude of gage."""
        return self.site_data.get("dec_long_va")

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def elevation(self) -> float:
        """Elevation of gage."""
        return self.site_data.get("alt_va")

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def mean_basin_elevation(self) -> float:
        """Average elevation of gage watershed."""
        row = [
            r for r in self.streamstats["characteristics"] if r["variableTypeID"] == 6
        ]  # Get ELEV param
        return row[0]["value"]

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def streamstats(self) -> pd.DataFrame:
        """Load AMS for this site."""
        r = requests.get(
            f"https://streamstats.usgs.gov/gagestatsservices/stations/{self.gage_id}"
        )
        return r.json()

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def ams(self) -> pd.DataFrame:
        """Load AMS for this site."""
        return get_ams(self.gage_id)

    @property
    def ams_vals(self) -> np.ndarray:
        """Convenient ams column selection."""
        return self.ams["peak_va"].values

    @property
    def missing_dates_ams(self) -> list:
        """Get missing dates for AMS."""
        return check_missing_dates(self.ams, "water_year")

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def flow_stats(self) -> pd.DataFrame:
        """Load flow statistics for this site."""
        return get_flow_stats(self.gage_id)

    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def get_daily_values(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load daily mean discharge for this site."""
        return get_daily_values(self.gage_id, start_date, end_date)

    def missing_dates_daily_values(self, start_date: str, end_date: str) -> list:
        """Get missing dates for mean daily value series."""
        return check_missing_dates(self.get_daily_values(start_date, end_date), "daily")

    @property
    @st.cache_data(
        hash_funcs={"hydroshift.utils.data_retrieval.Gage": lambda x: hash(x.gage_id)},
        max_entries=MAX_CACHE_ENTRIES
    )
    def monthly_values(self) -> pd.DataFrame:
        """Load monthly mean discharge for this site."""
        return get_monthly_values(self.gage_id)

    @property
    def missing_dates_monthly_values(self) -> list:
        """Get missing dates for mean monthly value series."""
        return check_missing_dates(self.monthly_values, "monthly")

    def get_regulation_summary(self, major_codes=["3", "9"]) -> List[str]:
        """Run regulation summary for gage."""
        df = self.ams
        df["water_year"] = df.index.year.where(df.index.month < 10, df.index.year + 1)

        regulation_years = {}

        for index, row in df.iterrows():
            if pd.notna(row.get("peak_cd")):
                codes = str(row["peak_cd"]).split(",")
                for code in codes:
                    code_str = code.strip()
                    try:
                        code_key = str(int(float(code_str)))  # Normalize numeric codes
                    except ValueError:
                        code_key = code_str

                    if code_key in REGULATION_MAP:
                        regulation_years.setdefault(code_key, set()).add(
                            row["water_year"]
                        )

        results = {"major": [], "minor": []}
        for code, years in regulation_years.items():
            grouped_year_ranges = group_consecutive_years(sorted(years))
            formatted_ranges = ", ".join(grouped_year_ranges)
            if code in major_codes:
                results["major"].append(
                    f"{REGULATION_MAP[code]} for water years {formatted_ranges}"
                )
            else:
                results["minor"].append(
                    f"{REGULATION_MAP[code]} for water years {formatted_ranges}"
                )

        return results

    def raise_warnings(self):
        """Create any high level data warnings."""
        if not self.ams_valid:
            st.error("Gage has no annual maxima series data available")
        if not self.dv_valid:
            st.error("Gage has no daily value data available")
        if not self.flow_stats_valid:
            st.error("Gage has no flow statistics data available")
        if not self.monthly_values_valid:
            st.error("Gage has no monthly flow statistics data available")

        if self.ams_valid:
            regulation_results = self.get_regulation_summary()
            if regulation_results["minor"]:
                for result in regulation_results["minor"]:
                    st.warning(result)
            if regulation_results["major"]:
                for result in regulation_results["major"]:
                    st.error(result)

    @property
    def has_regional_skew(self) -> bool:
        """Check if gage has regional skew available."""
        return self.regional_skew is not None

    @property
    def regional_skew(self) -> float:
        """The skew value from the PeakFQ skew map, if one exists."""
        raster = get_skew_raster()
        try:
            val = [i for i in raster.sample([(self.longitude, self.latitude)])][0][0]
            if val in raster.nodatavals:
                return None
        except (KeyError, IndexError):
            return None
        if val == 9999:  # California Eq. from USGS SIR 2010-5260 NL-ELEV eq
            val = (0 - 0.62) + 1.3 * (
                1 - np.exp(0 - ((self.mean_basin_elevation) / 6500) ** 2)
            )
        return val

    @property
    def ams_valid(self) -> bool:
        """Whether this gage has AMS data."""
        sub = self.data_catalog[self.data_catalog["data_type_cd"] == "pk"]
        if len(sub) > 0:
            if sub["count_nu"].values[0] > 0:
                return True
        return False

    @property
    def dv_valid(self) -> bool:
        """Whether this gage has daily value data."""
        sub = self.data_catalog[(self.data_catalog["data_type_cd"] == "dv") & (self.data_catalog["parm_cd"] == "00060")]
        if len(sub) > 0:
            if sub["count_nu"].values[0] > 0:
                return True
        return False

    @property
    def flow_stats_valid(self) -> bool:
        """Whether this gage has flow statistics data."""
        return self.flow_stats is not None

    @property
    def monthly_values_valid(self) -> bool:
        """Whether this gage has flow statistics data."""
        return self.monthly_values is not None



@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def get_ams(gage_id):
    """Fetches Annual Maximum Series (AMS) peak flow data for a given gage."""
    try:
        if gage_id == "testing":
            df = fake_ams()
        else:
            df = nwis.get_record(service="peaks", sites=[gage_id], ssl_check=True)
    except NoSitesError:
        logging.warning(f"Peaks could not be found for gage id: {gage_id}")
        return pd.DataFrame()

    df["season"] = ((df.index.month % 12 + 3) // 3).map(
        {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
    )  # TODO: should add labels like Winter(JFM), Spring(AMJ), etc

    df = df.dropna(subset="peak_va")
    return df


@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def get_flow_stats(gage_id):
    """Fetches flow statistics for a given gage."""
    try:
        df = nwis.get_stats(sites=gage_id, parameterCd="00060", ssl_check=True)[0]
    except IndexError:
        logging.warning(f"Flow stats could not be found for gage_id: {gage_id}")
        return None

    return df


@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def load_site_data(gage_number: str) -> dict:
    """Query NWIS for site information"""
    try:
        resp = nwis.get_record(sites=gage_number, service="site", ssl_check=True)

    except ValueError:
        raise ValueError(f"Gage {gage_number} not found")

    return {
        "site_no": resp["site_no"].iloc[0],
        "station_nm": resp["station_nm"].iloc[0],
        "dec_lat_va": float(resp["dec_lat_va"].iloc[0]),
        "dec_long_va": float(resp["dec_long_va"].iloc[0]),
        "drain_area_va": resp["drain_area_va"].iloc[0],
        "huc_cd": resp["huc_cd"].iloc[0],
        "alt_va": resp["alt_va"].iloc[0],
        "alt_datum_cd": resp["alt_datum_cd"].iloc[0],
    }

@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def get_site_catalog(gage_number: str) -> dict:
    """Query NWIS for site information"""
    try:
        df = nwis.what_sites(sites=gage_number, seriesCatalogOutput='true', ssl_check=True)[0]
    except Exception as e:
        print(str(e))
        print(traceback.format_exc())
    return df


@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def get_daily_values(gage_id, start_date, end_date):
    """Fetches mean daily flow values for a given gage."""
    try:
        dv = nwis.get_dv(gage_id, start_date, end_date, ssl_check=True)[0]
    except Exception:
        logging.warning(f"Daily Values could not be found for gage_id: {gage_id}")
        return None

    return dv


@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def get_monthly_values(gage_id):
    """Fetches mean monthly flow values for a given gage and assigns a datetime column based on the year and month."""
    try:
        mv = nwis.get_stats(gage_id, statReportType="monthly", ssl_check=True, parameterCode = "00060")[0]
    except Exception:
        logging.warning(f"Monthly Values could not be found for gage_id: {gage_id}")
        return None

    mv = mv.rename(columns={"year_nu": "year", "month_nu": "month"})

    mv["date"] = pd.to_datetime(mv[["year", "month"]].assign(day=1))

    mv = mv.sort_values("date")

    return mv


def check_missing_dates(df, freq):
    """Checks for missing dates in a DataFrame.

    Parameters
    ----------
    df (pd.DataFrame): The DataFrame containing time-series data.
    freq (str): Either 'daily', 'monthly', or 'water_year' to specify the type of data.

    """
    if freq == "daily":
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index("datetime")
        full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")

    elif freq == "monthly":
        df["date"] = pd.to_datetime(df["date"])
        full_range = pd.date_range(
            start=df["date"].min(), end=df["date"].max(), freq="MS"
        )

    elif freq == "water_year":
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index("datetime")

        df["water_year"] = df.index.year.where(df.index.month < 10, df.index.year + 1)

        full_water_years = set(
            range(df["water_year"].min(), df["water_year"].max() + 1)
        )
        existing_water_years = set(df["water_year"])
        missing_years = sorted(full_water_years - existing_water_years)

        return missing_years
    else:
        raise ValueError("Invalid frequency. Use 'daily', 'monthly', or 'water_year'.")

    missing_dates = full_range.difference(df.index if freq == "daily" else df["date"])

    return list(missing_dates)


def fake_ams() -> pd.DataFrame:
    """Generate a timeseries from two distributions."""
    rs = 1
    rvs = []
    segments = [
        {"length": 50, "loc": 1000, "scale": 50, "c": 0.1},
        {"length": 50, "loc": 900, "scale": 500, "c": 0.5},
        {"length": 50, "loc": 1000, "scale": 100, "c": 0.1},
    ]
    for s in segments:
        length = s["length"]
        params = {k: v for k, v in s.items() if k != "length"}
        dist = genpareto(**params)
        rvs.append(dist.rvs(size=length, random_state=rs))
        rs += 1

    rvs = np.concatenate(rvs, axis=0)
    dates = pd.date_range(start="1900-01-01", periods=len(rvs), freq="YE")
    water_year = dates.year
    df = pd.DataFrame(
        {"datetime": dates, "peak_va": rvs, "water_year": water_year}
    ).set_index("datetime")
    return df


@st.cache_resource
def get_skew_raster():
    """Load the skew raster into memory."""
    return rasterio.open(
        __file__.replace("utils/data_retrieval.py", "data/skewmap_4326.tif")
    )
