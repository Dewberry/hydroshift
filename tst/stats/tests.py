import numpy as np
import requests
from scipy.stats import cramervonmises_2samp, ks_2samp, mannwhitneyu, mood

from tst.errors import ShortTimeSeries
from tst.start_r_server import start_server


class ChangePointModel:
    """Generic change point model."""

    burn_in = 20

    def test_statistic(self, s1: np.ndarray, s2: np.ndarray) -> float:
        """Calculate test statistic."""
        return 0

    def validate_ts(self, ts: np.ndarray):
        """Make sure timeseries meets test requirements."""
        if len(ts) < (2 * self.burn_in):
            msg = f"Attempted KS test with burn in period of {self.burn_in}, but timeseries length was only {len(ts)}"
            raise ShortTimeSeries(msg)

    def detect_change_point(self, ts: np.ndarray) -> tuple[np.ndarray, int]:
        """Analyze a changepoint model for the class test."""
        self.validate_ts(ts)
        pvals = [0] * self.burn_in
        for ind in range(self.burn_in, len(ts) - self.burn_in):
            s1 = ts[:ind]
            s2 = ts[ind:]
            pvals.append(self.test_statistic(s1, s2))
        pvals.extend([0] * self.burn_in)
        cp = np.argmax(pvals)
        return pvals, cp


class KolmogorovSmirnovCPM(ChangePointModel):

    def test_statistic(self, s1, s2):
        pval = ks_2samp(s1, s2).statistic
        return self.kim_correction(len(s1), len(s2), pval)

    def kim_correction(self, n0: int, n1: int, ks_stat: float):
        """Apply Kim (1969) continuity correction to the KS statistic."""
        # See https://github.com/Quentin62/cpm/blob/9bc45141c78790d6fabbc9fa8907078bd69a7772/src/ChangePointModelKS.cpp
        # TODO:  Make sure n0 and n1 are indexing the same way as github and that we don't have to +1 or -1 or something
        # Ensure n0 >= n1
        if n1 > n0:
            n0, n1 = n1, n0

        # Apply correction based on the ratio of n0 and n1
        if n0 > 2 * n1:
            correction = 1 / (2 * np.sqrt(n0))
        elif n0 % n1 == 0:
            correction = 2 / (3 * np.sqrt(n0))
        else:
            correction = 2 / (5 * np.sqrt(n0))

        # Adjust KS statistic
        corrected_stat = ks_stat * np.sqrt((n0 * n1) / (n0 + n1)) + correction

        return corrected_stat


class CramerVonMisesCPM(ChangePointModel):

    def test_statistic(self, s1, s2):
        stat = cramervonmises_2samp(s1, s2).statistic
        return self.adjust_for_sample_size(stat, s1, s2)

    def adjust_for_sample_size(self, statistic: float, s1: np.ndarray, s2: np.ndarray) -> float:
        """Adjust the statistic for sample size."""
        # https://github.com/Quentin62/cpm/blob/9bc45141c78790d6fabbc9fa8907078bd69a7772/src/ChangePointModelCVM.cpp
        n0 = len(s1)
        n1 = len(s2)
        N = n0 + n1
        prod = n0 * n1
        mu = 1 / 6 + 1 / (6 * N)
        sigma = np.sqrt((1 / 45) * ((N + 1) / (N**2)) * ((4 * prod * N - 3 * (n1**2 + n0**2) - 2 * prod) / (4 * prod)))
        return (statistic * (prod) / (N**2) - mu) / sigma


class LepageCPM(ChangePointModel):

    # Ross, G. J., Tasoulis, D. K., Adams, N. M. (2011)– A Nonparametric Change-Point Model for Streaming Data, Technometrics, 53(4)

    def test_statistic(self, s1, s2):
        # Initial test statistics
        mood_stat = mood(s1, s2).statistic
        mw_stat = mannwhitneyu(s1, s2).statistic

        # Normalize
        n0 = len(s1)
        n1 = len(s2)
        N = n0 + n1

        mw_null_mean = n0 * n1 * 0.5
        mw_null_sd = (n0 * n1 * (n0 + n1 + 1) / 12) ** 0.5
        mw_stat = abs(mw_null_mean - mw_stat) / mw_null_sd

        mood_null_mean = n0 * ((N**2) - 1) / 12
        mood_null_sd = (n0 * n1 * (N + 1) * ((N**2) - 4) / 180) ** 2
        mood_stat = abs(mood_null_mean - mood_stat) / mood_null_sd
        return (mood_stat**2) + (mw_stat**2)


class MoodCPM(ChangePointModel):

    def test_statistic(self, s1, s2):
        n0 = len(s1)
        n1 = len(s2)
        N = n0 + n1
        mood_null_mean = n0 * ((N**2) - 1) / 12
        mood_null_sd = (n0 * n1 * (N + 1) * ((N**2) - 4) / 180) ** 2
        mood_stat = abs(mood_null_mean - mood(s1, s2).statistic) / mood_null_sd
        return mood_stat


def ks_cpm(ts: np.ndarray, burn_in: int = 20) -> tuple[np.ndarray, int]:
    """Analyze a changepoint model for the Kolmogorov-Smirnov test."""
    cpm = KolmogorovSmirnovCPM()
    cpm.burn_in = burn_in
    return cpm.detect_change_point(ts)


def cvm_cpm(ts: np.ndarray, burn_in: int = 20) -> tuple[np.ndarray, int]:
    """Analyze a changepoint model for the Cramer Von Mises test."""
    cpm = CramerVonMisesCPM()
    cpm.burn_in = burn_in
    return cpm.detect_change_point(ts)


def lapage_cpm(ts: np.ndarray, burn_in: int = 20) -> tuple[np.ndarray, int]:
    """Analyze a changepoint model for the Cramer Von Mises test."""
    cpm = LepageCPM()
    cpm.burn_in = burn_in
    return cpm.detect_change_point(ts)


def cpm_process_stream(x: np.ndarray, cpm_type: str) -> np.ndarray:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"x": x, "cpm_type": cpm_type}
    url = "http://127.0.0.1:9999/process_stream"
    response = requests.get(url, params=payload)
    return response.json()
