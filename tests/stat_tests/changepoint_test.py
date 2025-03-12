from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.stats import genpareto

from tst.stats.tests import cvm_cpm, ks_cpm, lapage_cpm

TESTS = {
    "1": {"p1_length": 50, "p2_length": 50, "change_types": ["loc"], "severity": 1.1},
    "2": {"p1_length": 50, "p2_length": 50, "change_types": ["loc", "scale"], "severity": 1.1},
    "3": {"p1_length": 50, "p2_length": 50, "change_types": ["scale"], "severity": 10},
}


def generate_timeseries(p1_length: int, p2_length: int, change_types: list[str], severity: float) -> np.ndarray:
    """Generate a timeseries from two distributions."""

    # Set up distributions
    parameters = {"p1": {"loc": 1000, "scale": 100, "c": 0.3}, "p2": {}}
    for p in parameters["p1"]:
        if p in change_types:
            parameters["p2"][p] = parameters["p1"][p] * severity
        else:
            parameters["p2"][p] = parameters["p1"][p]
    p1_dist = genpareto(**parameters["p1"])
    p2_dist = genpareto(**parameters["p2"])

    # Generate RVs
    rs = 1
    p1 = p1_dist.rvs(size=p1_length, random_state=rs)
    p2 = p2_dist.rvs(size=p2_length, random_state=rs)

    return np.append(p1, p2, axis=0)


def diagnostic_plot(ts: np.ndarray, pvals: np.ndarray, cp: int, out_path: str):
    """Make a diagnostic plot for a test."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(nrows=2, figsize=(10, 6), sharex=True)
    axs[0].scatter(range(len(ts)), ts, ec="#4d64fa", fc="none")
    axs[1].scatter(range(len(ts)), pvals, c="k", s=4)
    axs[1].plot(range(len(ts)), gaussian_filter1d(pvals, sigma=2), ls="dashed", lw=2, c="#fa954d")
    axs[0].axvline(cp, c="r", ls="dashed")
    axs[0].set_facecolor("whitesmoke")
    axs[1].set_facecolor("whitesmoke")
    axs[1].set_xlabel("Time")
    axs[0].set_ylabel("Magnitude")
    axs[1].set_ylabel("Test pvalue")
    fig.tight_layout()
    fig.savefig(out_path)


def test_ks_cpm():
    """Test the kolmogorov-smirnov change point model."""

    for t in TESTS:
        ts = generate_timeseries(**TESTS[t])
        pvals, cp = ks_cpm(ts)

        diagnostic_plot(ts, pvals, cp, f"tests/stat_tests/ks/{t}.png")
        cp_ = TESTS[t]["p1_length"]
        assert cp == cp_, f"Kolmogorov-Smirnov CPM failed to detect correct changepoint. Result: {cp}, Truth: {cp_}"


def test_cvm_cpm():
    """Test the Cramer-von-mises change point model."""

    for t in TESTS:
        ts = generate_timeseries(**TESTS[t])
        pvals, cp = cvm_cpm(ts)

        diagnostic_plot(ts, pvals, cp, f"tests/stat_tests/cvm/{t}.png")
        cp_ = TESTS[t]["p1_length"]
        assert cp == cp_, f"Cramer Von-Mises CPM failed to detect correct changepoint. Result: {cp}, Truth: {cp_}"


def test_lepage_cpm():
    """Test the Cramer-von-mises change point model."""

    for t in TESTS:
        ts = generate_timeseries(**TESTS[t])
        pvals, cp = lapage_cpm(ts)

        diagnostic_plot(ts, pvals, cp, f"tests/stat_tests/lepage/{t}.png")
        cp_ = TESTS[t]["p1_length"]
        assert abs(cp - cp_) < 10, f"Lepage CPM failed to detect correct changepoint. Result: {cp}, Truth: {cp_}"


if __name__ == "__main__":
    test_lepage_cpm()
    # test_cvm_cpm()
    # test_ks_cpm()
