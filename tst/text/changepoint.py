test_description = """
A changepoint analysis was performed on the series of annual flood peaks Using the change point model of Ross (2015). For each data in the timeseries, the distribution of flood peaks leading up to that date were compared with the distribution after that date using a variety of statistical tests

 - **Mood**: Measures changes in the variance of the peak series.
 - **Mann-Whitney**: Measures changes in the mean of the peak series.
 - **Lepage**: Combines both Mood and Mann-Whitney statistics into one.
 - **Kolmogorov-Smirnov**: Measures changes in the overall distribution of flood peaks.
 - **Cramer-von-Mises**: Measures changes in the overall distribution of flood peaks.

These test statistics were utilized in two distinct ways in this analysis.  A preliminary "coarse" analysis is performed by evaluating the test statistic at each date of the timeseries and using a two-sample test to determine the statistical significance of the distribution differences.  The P-values from this analysis are shown in the second panel of Figure 1.  The second "detailed" analysis involved scanning the timeseries for areas where the statistical tests exceed a significant level of difference, at which point the series is split, and the test statistic is calculated on values from the split to each date. The resulting change points are shown as dashed red lines in the top panel of Figure 1.

For this analysis, a threshold of 1 in {} was selected to identify change points in the detailed analysis.  Furthermore, a "burn-in" period of {} years was selected to ignore singificant change points in the first and last {} years of the record due to the influence of small sample sizes.
"""
references = """
References:

Gordon J. Ross (2015)., "Parametric and Nonparametric Sequential Change Detection in R: The cpm Package.", Journal of Statistical Software, 66(3), 1-20., https://www.jstatsoft.org/v66/i03/.
"""
