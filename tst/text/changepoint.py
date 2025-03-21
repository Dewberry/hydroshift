"""Storage for large blocks of changepoint app text."""

test_description = """
A changepoint analysis was performed on the series of annual flood peaks Using the change point model of Ross (2015). For each date in the timeseries, the distribution of flood peaks leading up to that date were compared with the distribution after that date using a variety of statistical tests

 - **Mood**: Measures changes in the variance of the peak series.
 - **Mann-Whitney**: Measures changes in the mean of the peak series.
 - **Lepage**: Combines both Mood and Mann-Whitney statistics into one.
 - **Kolmogorov-Smirnov**: Measures changes in the overall distribution of flood peaks.
 - **Cramer-von-Mises**: Measures changes in the overall distribution of flood peaks.

These test statistics were utilized in two distinct ways in this analysis.  A static analysis was performed by evaluating the test statistic at each date of the timeseries and using a two-sample test to determine the statistical significance of the distribution differences.  The P-values from this analysis are shown in the second panel of Figure 1.
A streaming analysis was performed by treating the data as a stream of values and repeating the static analysis after each new value was added. If the test statistic exceeds a specified threshold at any point within the subseries, a changepoint is marked, and a new data series is initialized for all further test statistics. The resulting change points are shown as dashed red lines in the top panel of Figure 1.

 - The threshold for identifying changepoints in the streaming analysis is defined using an Average Run Length (ARL0) parameter. ARL0 reflects the frequency with which a false positive would be raised on a stationary timeseries (e.g., for an ARL0 of 1,000 a false changepoint would be identified on a stationary timeseries on average every 1,000 samples.).  For this analysis, an ARL0 of {} was used.
 - A burn-in period of {} years was selected to ignore singificant change points in the first and last {} years of the record due to the influence of small sample sizes.

"""
references = """
Gordon J. Ross (2015)., "Parametric and Nonparametric Sequential Change Detection in R: The cpm Package.", Journal of Statistical Software, 66(3), 1-20., https://www.jstatsoft.org/v66/i03/.
"""
