from math import comb

import numpy as np
import pandas as pd
import rasterio
import streamlit as st
from scipy import stats


@st.cache_data
def get_skew_raster():
    """Load the skew raster into memory."""
    return rasterio.open(__file__.replace("ffa.py", "skewmap_4326.tif"))


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


@st.cache_data
def log_pearson_iii(
    peak_flows: pd.Series,
    standard_return_periods: list = [1.1, 2, 5, 10, 25, 50, 100, 500],
    method: str = "MLE",
    coords: list = None,
):
    log_flows = np.log10(peak_flows.values)
    if method == "MM":
        skew_log, mean_log, std_log = stats.pearson3.fit(log_flows, method="MM")
    elif method == "MLE":
        skew_log, mean_log, std_log = stats.pearson3.fit(log_flows, method="MLE")
    elif method == "LMOM":
        mean_log, std_log, skew_log = l_moments(log_flows)

    if coords:
        src = get_skew_raster()
        tmp_skew = src.sample(coords[0:2])
        if tmp_skew == 9999:  # CA Equation
            tmp_skew = (0 - 0.62) + 1.3 * (1 - np.exp(0 - ((coords[2]) / 6500) ^ 2))
        if not np.isnan(tmp_skew):
            skew_log = tmp_skew

    return {
        rp: int(10 ** stats.pearson3(skew=skew_log, loc=mean_log, scale=std_log).ppf(1 - 1 / rp))
        for rp in standard_return_periods
    }
