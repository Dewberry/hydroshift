from dataclasses import dataclass, field
from math import comb
from typing import List

import numpy as np
import pandas as pd
from scipy.stats import pearson3, rv_continuous

from hydroshift.utils.data_retrieval import Gage


@dataclass
class LP3Analysis:
    """A log-pearson type 3 analysis."""

    gage_id: str
    peaks: list
    use_map_skew: bool = False
    est_method: str = "MLE"
    label: str = ""
    return_periods: List[str] = field(
        default_factory=lambda: [1.1, 2, 5, 10, 25, 50, 100, 500]
    )

    # TODO:  Add california equation.  Likely best to subclass this.

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
        if self.use_map_skew:
            skew_log = self.weighted_skew
        return mean_log, std_log, skew_log

    @property
    def station_skew(self) -> tuple[float]:
        """Skew of peaks."""
        return pearson3.fit(self.log_peaks, method="MM")[0]

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
        ris = [str(i) for i in self.return_periods]
        return pd.DataFrame({"Recurrence Interval (years)": ris, "Discharge (cfs)": qs})

    @property
    def map_skew(self):
        """The skew value from the PeakFQ skew map, if one exists."""
        gage = Gage(self.gage_id)
        return gage.regional_skew

    @property
    def mse_station_skew(self) -> float:
        """Weighted station skew using USGS B17B method."""
        abs_g = abs(self.station_skew)
        if abs_g <= 0.9:
            a = -0.33 + (0.08 * abs_g)
        else:
            a = -0.52 + (0.3 * abs_g)
        if abs_g <= 1.5:
            b = 0.94 - (0.26 * abs_g)
        else:
            a = 0.55
        return 10 ** (a - (b * np.log10(len(self.peaks) / 10)))

    @property
    def weighted_skew(self) -> float:
        """Weighted station skew using USGS B17B method."""
        g_s = self.station_skew  # Station Skew
        g_g = self.map_skew  # Generalized skew
        mse_s = self.mse_station_skew  # MSE of station skew
        mse_g = 0.302  # From peakfq user manual page 7.  TODO: Update for Cali equation

        # From Handbook of hydrology pg 18.44
        g_weighted = ((g_s / mse_s) + (g_g / mse_g)) / ((1 / mse_s) + (1 / mse_g))
        return g_weighted


def l_moments(series):
    """Calculate first three L moments."""
    ### From Stedinger 1993 around page 7 (section 18.6.1) ###
    series = np.sort(series)[::-1]
    n = len(series)
    b_values = list()
    # This method could be streamlined, but as-is, it's easily debugged
    for r in range(4):
        running_sum = list()
        for j in range(n - r):
            cur = (comb(n - (j + 1), r) * series[j]) / comb(n - 1, r)
            running_sum.append(cur)
        running_sum = sum(running_sum)
        b = running_sum / n
        b_values.append(b)

    l1 = b_values[0]
    l2 = (2 * b_values[1]) - b_values[0]
    l3 = (6 * b_values[2]) - (6 * b_values[1]) + (1 * b_values[0])
    return l1, l2, l3
