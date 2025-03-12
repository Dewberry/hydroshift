import numpy as np
from scipy.stats import ks_2samp

from tst.errors import ShortTimeSeries


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


def ks_cpm(ts: np.ndarray, burn_in: int = 20) -> tuple[np.ndarray, int]:
    """Analyze a changepoint model for the Kolmogorov-Smirnov test."""
    cpm = KolmogorovSmirnovCPM()
    cpm.burn_in = burn_in
    return cpm.detect_change_point(ts)
