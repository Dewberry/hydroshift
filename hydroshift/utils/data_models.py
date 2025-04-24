from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import pearson3, rv_continuous

from hydroshift.utils.data_retrieval import (
    check_missing_dates,
    get_ams,
    get_daily_values,
    get_flow_stats,
    get_monthly_values,
    load_site_data,
)
from hydroshift.utils.ffa import l_moments


class Gage:
    """A USGS Gage."""

    def __init__(self, gage_id: str):
        """Construct class."""
        self.gage_id = gage_id
        self.site_data = load_site_data(gage_id)

    @property
    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
    def latitude(self) -> float:
        """Latitude of gage."""
        return self.site_data.get("dec_lat_va")

    @property
    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
    def longitude(self) -> float:
        """Longitude of gage."""
        return self.site_data.get("dec_long_va")

    @property
    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
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
    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
    def flow_stats(self) -> pd.DataFrame:
        """Load flow statistics for this site."""
        return get_flow_stats(self.gage_id)

    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
    def get_daily_values(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load daily mean discharge for this site."""
        return get_daily_values(self.gage_id, start_date, end_date)

    @property
    def missing_dates_daily_values(self, start_date: str, end_date: str) -> list:
        """Get missing dates for mean daily value series."""
        return check_missing_dates(self.get_daily_values(start_date, end_date), "daily")

    @st.cache_data(hash_funcs={"hydroshift.utils.data_models.Gage": lambda x: hash(x.gage_id)})
    def get_monthly_values(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load monthly mean discharge for this site."""
        return get_monthly_values(self.gage_id, start_date, end_date)

    @property
    def missing_dates_monthly_values(self, start_date: str, end_date: str) -> list:
        """Get missing dates for mean monthly value series."""
        return check_missing_dates(self.get_monthly_values(start_date, end_date), "monthly")

    def raise_warnings(self):
        """Create any high level data warnings."""
        pass

    @property
    def has_regional_skew(self):
        """Check if gage has regional skew available."""
        return False


@dataclass
class LP3Analysis:
    """A log-pearson type 3 analysis."""

    gage_id: str
    peaks: list
    regional_skew: float = None
    est_method: str = "MLE"
    label: str = ""
    return_periods: List[str] = field(default_factory=lambda: [1.1, 2, 5, 10, 25, 50, 100, 500])

    def __post_init__(self):
        """Customize init."""
        self.peaks = np.sort(self.peaks)

    @property
    def log_peaks(self) -> np.ndarray:
        """Log 10 of peaks."""
        return np.log10(self.peaks)

    @property
    def parameters(self) -> tuple[float]:
        """Sample parameters for LP3 distribution."""
        if self.est_method == "MOM":
            skew_log, mean_log, std_log = pearson3.fit(self.log_peaks, method="MM")
        elif self.est_method == "MLE":
            skew_log, mean_log, std_log = pearson3.fit(self.log_peaks, method="MLE")
        elif self.est_method == "LMOM":
            mean_log, std_log, l3 = l_moments(self.log_peaks)
            skew_log = l3 / (std_log * 0.7797)  # pseudo-stdev
        if self.regional_skew is not None:
            skew_log = self.regional_skew
        return mean_log, std_log, skew_log

    @property
    def distribution(self) -> rv_continuous:
        """The fitted LP3 distribution."""
        params = self.parameters
        return pearson3(params[2], params[0], params[1])

    @property
    def plotting_positions(self) -> tuple[np.ndarray]:
        """Empirical flood frequency curve."""
        aep = np.arange(1, len(self.peaks) + 1)[::-1] / (len(self.peaks) + 1)
        return (aep, self.peaks)

    @property
    def ffa_quantiles(self) -> tuple[np.ndarray]:
        """Calculate some recurrence intervals from fitted distribution."""
        ris = np.array(self.return_periods)
        aeps = 1 / ris
        qs = np.power(10, self.distribution.ppf(1 - aeps)).astype(int)
        return (aeps, qs)

    @property
    def quantile_df(self):
        """Put quantiles into a dataframe."""
        _, qs = self.ffa_quantiles
        return pd.DataFrame({"Recurrence Interval (years)": self.return_periods, "Discharge (cfs)": qs})
