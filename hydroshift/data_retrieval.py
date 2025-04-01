import logging

import numpy as np
import pandas as pd
import scipy.stats as stats
from dataretrieval import NoSitesError, nwis
from scipy.stats import genpareto


def get_ams(gage_id, return_lp3_stats=False):
    """Fetches Annual Maximum Series (AMS) peak flow data for a given gage."""
    try:
        if gage_id == "testing":
            df = fake_ams()
        else:
            df = nwis.get_record(service="peaks", sites=[gage_id], ssl_check=False)
    except NoSitesError:
        logging.warning(f"Peaks could not be found for gage id: {gage_id}")
        return None

    df["season"] = ((df.index.month % 12 + 3) // 3).map({1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"})

    missing_years = check_missing_dates(df, "water_year")

    if return_lp3_stats:
        return log_pearson_iii(df["peak_va"]), missing_years
    else:
        return df, missing_years


def get_flow_stats(gage_id):
    """Fetches flow statistics for a given gage."""
    try:
        df = nwis.get_stats(sites=gage_id, ssl_check=False)[0]
    except IndexError:
        logging.warning(f"Flow stats could not be found for gage_id: {gage_id}")
        return None

    return df


def load_site_data(gage_number: str) -> dict:
    """Query NWIS for site information"""
    try:
        resp = nwis.get_record(sites=gage_number, service="site", ssl_check=False)

    except ValueError:
        raise ValueError(f"Gage {gage_number} not found")

    return {
        "Site Number": resp["site_no"].iloc[0],
        "Station Name": resp["station_nm"].iloc[0],
        "Latitude": float(resp["dec_lat_va"].iloc[0]),
        "Longitude": float(resp["dec_long_va"].iloc[0]),
        "Drainage Area": resp["drain_area_va"].iloc[0],
        "HUC Code": resp["huc_cd"].iloc[0],
        "Elevation Datum": resp["alt_datum_cd"].iloc[0],
    }


def log_pearson_iii(peak_flows: pd.Series, standard_return_periods: list = [2, 5, 10, 25, 50, 100, 500]):
    log_flows = np.log10(peak_flows.values)
    mean_log = np.mean(log_flows)
    std_log = np.std(log_flows, ddof=1)
    skew_log = stats.skew(log_flows)

    return {
        str(rp): int(10 ** (mean_log + stats.pearson3.ppf(1 - 1 / rp, skew_log) * std_log))
        for rp in standard_return_periods
    }


def get_daily_values(gage_id, start_date, end_date):
    """Fetches mean daily flow values for a given gage."""
    try:
        dv = nwis.get_dv(gage_id, start_date, end_date, ssl_check=False)[0]
    except Exception:
        logging.warning(f"Daily Values could not be found for gage_id: {gage_id}")
        return None

    missing_dates = check_missing_dates(dv, "daily")

    return dv, missing_dates


def get_monthly_values(gage_id):
    """Fetches mean monthly flow values for a given gage and assigns a datetime column based on the year and month."""
    try:
        mv = nwis.get_stats(gage_id, statReportType="monthly", ssl_check=False)[0]
    except Exception:
        logging.warning(f"Monthly Values could not be found for gage_id: {gage_id}")
        return None

    mv = mv.rename(columns={"year_nu": "year", "month_nu": "month"})

    mv["date"] = pd.to_datetime(mv[["year", "month"]].assign(day=1))

    mv = mv.sort_values("date")
    missing_dates = check_missing_dates(mv, "monthly")

    return mv, missing_dates


def check_missing_dates(df, freq):
    """
    Checks for missing dates in a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame containing time-series data.
    freq (str): Either 'daily', 'monthly', or 'water_year' to specify the type of data.
    """

    if freq == "daily":
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index("datetime")
        full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")

    elif freq == "monthly":
        df["date"] = pd.to_datetime(df["date"])
        full_range = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="MS")

    elif freq == "water_year":
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index("datetime")

        df["water_year"] = df.index.year.where(df.index.month < 10, df.index.year + 1)

        full_water_years = set(range(df["water_year"].min(), df["water_year"].max() + 1))
        existing_water_years = set(df["water_year"])
        missing_years = sorted(full_water_years - existing_water_years)

        return missing_years
    else:
        raise ValueError("Invalid frequency. Use 'daily', 'monthly', or 'water_year'.")

    missing_dates = full_range.difference(df.index if freq == "daily" else df["date"])

    return list(missing_dates)


def fake_ams() -> pd.DataFrame:
    """Generate a timeseries from two distributions."""
    rs = 1
    rvs = []
    segments = [
        {"length": 50, "loc": 1000, "scale": 50, "c": 0.1},
        {"length": 50, "loc": 900, "scale": 500, "c": 0.5},
        {"length": 50, "loc": 1000, "scale": 100, "c": 0.1},
    ]
    for s in segments:
        length = s["length"]
        params = {k: v for k, v in s.items() if k != "length"}
        dist = genpareto(**params)
        rvs.append(dist.rvs(size=length, random_state=rs))
        rs += 1

    rvs = np.concatenate(rvs, axis=0)
    dates = pd.date_range(start="1900-01-01", periods=len(rvs), freq="YE")
    water_year = dates.year
    df = pd.DataFrame({"datetime": dates, "peak_va": rvs, "water_year": water_year}).set_index("datetime")
    return df
