"""Shared variables."""

# UI
DEFAULT_GAGE = "01151500"

### R Server ###
R_SERVER_PORT = 9999
R_SERVER_URL = f"http://127.0.0.1:{R_SERVER_PORT}"

### Changepoint Analysis ###
VALID_ARL0S = [
    370,
    500,
    600,
    700,
    800,
    900,
    1000,
    2000,
    3000,
    4000,
    5000,
    6000,
    7000,
    8000,
    9000,
    10000,
    20000,
    30000,
    40000,
    50000,
]
METRICS = ["Cramer-von-Mises", "Kolmogorov-Smirnov", "Lepage", "Mann-Whitney", "Mood"]

### External URLs ###
NWIS_URL = "https://waterdata.usgs.gov/nwis?"
PEAKFQ_URL = "https://www.usgs.gov/tools/peakfq"

### Text snippets ###
DATA_SOURCES_STR = f"Data: [USGS NWIS]({NWIS_URL}) and [USGS PEAKFQ]({PEAKFQ_URL})"

CP_F1_CAPTION = "**Figure 1.** Statistical changepoint analysis."
CP_T1_CAPTION = "**Table 1.** Results of the changepoint analysis, listing dates when a significant change was identified for each test statistic."
CP_F2_CAPTION = "**Figure 2.** Modified flood frequency analysis."
CP_T2_CAPTION = "**Table 2.** Modified flood quantiles."
