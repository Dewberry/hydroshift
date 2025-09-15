"""Shared variables."""

# UI
DEFAULT_GAGE = "01151500"

### R Server ###
R_SERVER_PORT = 9999
R_SERVER_URL = f"http://127.0.0.1:{R_SERVER_PORT}"

### FFA ###

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
DEWBERRY_URL = "https://www.dewberry.com/"
GITHUB_URL = "https://github.com/Dewberry/non-stationarity-tool"
ADMIN_EMAIL = "klawson@dewberry.com"

### Text snippets ###
DATA_SOURCES_STR = f"Data: [USGS NWIS]({NWIS_URL}) and [USGS PEAKFQ]({PEAKFQ_URL})"

CP_F1_CAPTION = "**Figure 1.** Statistical changepoint analysis."
CP_T1_CAPTION = "**Table 1.** Results of the changepoint analysis, listing dates when a significant change was identified for each test statistic."
CP_F2_CAPTION = "**Figure 2.** Modified flood frequency analysis."
CP_T2_CAPTION = "**Table 2.** Modified flood quantiles."

### MISC ###
REGULATION_MAP = {
    "3": "Discharge affected by Dam Failure",
    "5": "Discharge affected to unknown degree by Regulation or Diversion",
    "6": "Discharge affected by Regulation or Diversion",
    "9": "Discharge due to Snowmelt, Hurricane, Ice-Jam or Debris Dam breakup",
    "C": "All or part of the record affected by Urbanization, Mining, Agricultural changes, Channelization, or other",
}

### IMAGES ###
def svg2text(path: str) -> str:
    with open(path, "r") as f:
        svg = f.read()
    if svg.startswith("<?xml"):
        svg = svg.split("?>", 1)[1]
    return svg.strip()
GITHUB_SVG = svg2text("hydroshift/images/github_logo.svg")
DEWBERRY_SVG = svg2text("hydroshift/images/dewberry_logo.svg")
MAIL_SVG = svg2text("hydroshift/images/mail_logo.svg")
