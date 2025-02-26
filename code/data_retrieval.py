from dataretrieval import nwis
import pandas as pd
from dataretrieval import nwis, NoSitesError
import logging
from datetime import datetime
import numpy as np
import scipy.stats as stats


def get_ams(gage_id, return_lp3_stats=False):
    """Fetches Annual Maximum Series (AMS) peak flow data for a given gage."""
    try:
        df = nwis.get_record(service="peaks", sites=[gage_id])
    except NoSitesError:
        logging.warning(f"Peaks could not be found for gage id: {gage_id}")
        return None

    df["season"] = ((df.index.month % 12 + 3) // 3).map({1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"})

    if return_lp3_stats:
        return log_pearson_iii(df["peak_va"])
    else:
        return df


def get_flow_stats(gage_id):
    """Fetches flow statistics for a given gage."""
    try:
        df = nwis.get_stats(sites=gage_id)[0]
    except IndexError:
        logging.warning(f"Flow stats could not be found for gage_id: {gage_id}")
        return None

    return df


def load_site_data(gage_number: str) -> dict:
    """Query NWIS for site information"""
    try:
        resp = nwis.get_record(sites=gage_number, service="site")
        return {
            "Site Number": resp["site_no"].iloc[0],
            "Station Name": resp["station_nm"].iloc[0],
            "Latitude": float(resp["dec_lat_va"].iloc[0]),
            "Longitude": float(resp["dec_long_va"].iloc[0]),
            "Drainage Area": resp["drain_area_va"].iloc[0],
            "HUC Code": resp["huc_cd"].iloc[0],
            "Elevation Datum": resp["alt_datum_cd"].iloc[0],
        }
    except Exception:
        return None


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
        dv = nwis.get_dv(gage_id, start_date, end_date)[0]
    except Exception:
        logging.warning(f"Daily Values could not be found for gage_id: {gage_id}")
        return None

    return dv


def get_monthly_values(gage_id):
    """Fetches mean monthly flow values for a given gage and assigns a datetime column based on the year and month."""
    try:
        mv = nwis.get_stats(gage_id, statReportType="monthly")[0]
    except Exception:
        logging.warning(f"Monthly Values could not be found for gage_id: {gage_id}")
        return None

    mv = mv.rename(columns={"year_nu": "year", "month_nu": "month"})

    mv["date"] = pd.to_datetime(mv[["year", "month"]].assign(day=1))

    mv = mv.sort_values("date")
    return mv
