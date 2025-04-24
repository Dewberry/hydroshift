"""Statistical tests for timeseries."""

from collections import defaultdict

import numpy as np
import pandas as pd
import requests

from hydroshift.consts import R_SERVER_URL
from hydroshift.rserver.start_r_server import start_server


def cpm_process_stream(x: np.ndarray, cpm_type: str, arl0: int = 1000, burn_in: int = 20) -> dict:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"x": x, "cpm_type": cpm_type, "ARL0": arl0, "startup": burn_in}
    url = f"{R_SERVER_URL}/process_stream"
    response = requests.get(url, params=payload)
    return response.json()


def cpm_detect_change_point_batch(x: np.ndarray, cpm_type: str) -> dict:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"x": x, "cpm_type": cpm_type}
    url = f"{R_SERVER_URL}/detect_change_point_batch"
    response = requests.get(url, params=payload)
    return response.json()


def get_batch_threshold(cpm_type: str, alpha: float, n: int) -> float:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"cpm_type": cpm_type, "alpha": alpha, "n": n}
    url = f"{R_SERVER_URL}/get_batch_threshold"
    response = requests.get(url, params=payload)
    return response.json()[0]


def cp_pvalue_batch(cpm_type: str, ts: np.ndarray) -> np.ndarray:
    """Get test batch test statistics and then covert to p values."""
    p_range = np.array([0.05, 0.01, 0.005, 0.001])
    thresholds = [get_batch_threshold(cpm_type, p, len(ts)) for p in p_range]
    res = cpm_detect_change_point_batch(ts, cpm_type)
    Ds = np.array(res["Ds"])
    idx = np.searchsorted(thresholds, Ds)
    return np.append([np.nan], p_range)[idx]


def analyze_ts(df: pd.DataFrame) -> dict:
    """Run all changepoint analyses on a timeseries."""
    # Setup
    ts = df["peak_va"].values
    pval_df = df[[]]
    cp_dict = defaultdict(list)
    metrics = ["Cramer-von-Mises", "Kolmogorov-Smirnov", "Lepage", "Mann-Whitney", "Mood"]

    # Process
    for metric in metrics:
        pval_df[metric] = cp_pvalue_batch(metric, ts)
        stream_res = cpm_process_stream(ts, metric)
        for cp in stream_res["changePoints"]:
            cp_dict[cp].append(metric)
    for cp in cp_dict:
        cp_dict[cp] = ", ".join(cp_dict[cp])
    return {"pval_df": pval_df, "cps": cp_dict}
