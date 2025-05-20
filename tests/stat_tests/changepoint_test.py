from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import genpareto

from hydroshift.utils.changepoint import (
    cpm_detect_change_point_batch,
    cpm_process_stream,
    get_batch_threshold,
)

TESTS = {
    "1": [{"length": 50, "loc": 1000, "scale": 100, "c": 0.3}, {"length": 50, "loc": 1300, "scale": 100, "c": 0.3}],
    "2": [{"length": 50, "loc": 1000, "scale": 100, "c": 0.3}, {"length": 50, "loc": 1050, "scale": 200, "c": 0.5}],
    "3": [
        {"length": 50, "loc": 1000, "scale": 100, "c": 0.3},
        {"length": 50, "loc": 900, "scale": 500, "c": 0.5},
        {"length": 50, "loc": 1000, "scale": 100, "c": 0.3},
    ],
}


def generate_timeseries(segments: list) -> np.ndarray:
    """Generate a timeseries from two distributions."""
    rs = 1
    rvs = []
    for s in segments:
        length = s["length"]
        params = {k: v for k, v in s.items() if k != "length"}
        dist = genpareto(**params)
        rvs.append(dist.rvs(size=length, random_state=rs))

    return np.concatenate(rvs, axis=0)


def diagnostic_plot(ts: np.ndarray, pvals: np.ndarray, cp: int, out_path: str):
    """Make a diagnostic plot for a test."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(nrows=2, figsize=(10, 6), sharex=True)
    axs[0].scatter(range(len(ts)), ts, ec="#4d64fa", fc="none")
    axs[1].scatter(range(len(ts)), pvals, c="k", s=4)
    axs[1].plot(range(len(ts)), gaussian_filter1d(pvals, sigma=2), ls="dashed", lw=2, c="#fa954d")
    if isinstance(cp, int):
        axs[0].axvline(cp, c="r", ls="dashed")
    elif isinstance(cp, list):
        for c in cp:
            axs[0].axvline(c, c="r", ls="dashed")
    axs[0].set_facecolor("whitesmoke")
    axs[1].set_facecolor("whitesmoke")
    axs[1].set_xlabel("Time")
    axs[0].set_ylabel("Magnitude")
    axs[1].set_ylabel("Test pvalue")
    fig.tight_layout()
    fig.savefig(out_path)


def diagnostic_plot_2(ts: np.ndarray, cps: list, out_path: str):
    """Make a diagnostic plot for a test."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(range(len(ts)), ts, ec="#4d64fa", fc="none")
    for cp in cps:
        ax.axvline(cp, c="r", ls="dashed")
    ax.set_facecolor("whitesmoke")
    ax.set_xlabel("Time")
    ax.set_ylabel("Magnitude")
    fig.tight_layout()
    fig.savefig(out_path)


def test_cpm(metric: str):
    """Test the a change point model for a given metric."""
    for t in TESTS:
        ts = generate_timeseries(TESTS[t])
        res = cpm_process_stream(ts, metric)
        cps = res["changePoints"]
        # diagnostic_plot_2(ts, cps, f"tests/stat_tests/{metric}/{t}.png")
        res = cpm_detect_change_point_batch(ts, metric)
        diagnostic_plot(ts, res["Ds"], cps, f"tests/stat_tests/{metric}/{t}.png")


def test_combo():
    """Merge all stats into ensemble."""
    ts = generate_timeseries(TESTS["1"])
    n = len(ts)
    p_series = []
    metrics = ["Cramer-von-Mises", "Kolmogorov-Smirnov", "Lepage", "Mann-Whitney", "Mood"]
    for metric in metrics:
        p_range = [0.05, 0.01, 0.005, 0.001]
        thresholds = [get_batch_threshold(metric, p, n) for p in p_range]
        res = cpm_detect_change_point_batch(ts, metric)
        Ds = res["Ds"]
        p_vals = np.interp(Ds, thresholds, p_range, left=np.nan, right=0.001)
        p_series.append(p_vals)

    fig, axs = plt.subplots(nrows=2, figsize=(10, 6), sharex=True)
    axs[0].scatter(range(len(ts)), ts, ec="#4d64fa", fc="none")
    for ind, s in enumerate(p_series):
        axs[1].scatter(range(len(s)), s, label=metrics[ind])
    axs[1].legend()
    axs[0].set_facecolor("whitesmoke")
    axs[1].set_facecolor("whitesmoke")
    axs[1].set_xlabel("Time")
    axs[0].set_ylabel("Magnitude")
    axs[1].set_ylabel("Test pvalue")
    fig.tight_layout()
    fig.savefig("combo.png")


if __name__ == "__main__":
    test_combo()
    # for metric in ["Cramer-von-Mises", "Kolmogorov-Smirnov", "Lepage", "Mann-Whitney", "Mood"]:
    #     test_cpm(metric)
