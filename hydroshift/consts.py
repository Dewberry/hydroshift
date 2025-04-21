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

REGULATION_MAP = {
    "3": "Discharge affected by Dam Failure",
    "5": "Discharge affected to unknown degree by Regulation or Diversion",
    "6": "Discharge affected by Regulation or Diversion",
    "9": "Discharge due to Snowmelt, Hurricane, Ice-Jam or Debris Dam breakup",
    "C": "All or part of the record affected by Urbanization, Mining, Agricultural changes, Channelization, or other",
}
