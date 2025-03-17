from collections import defaultdict
from dataclasses import dataclass, field
from io import BytesIO

import pandas as pd
import streamlit as st
from data_retrieval import (
    get_ams,
)
from docx import Document
from plots import combo_cpm

from tst.stats.tests import cp_pvalue_batch, cpm_process_stream
from tst.text.changepoint import references, test_description

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


@dataclass
class ChangePointAnalysis:
    data: dict = field(default_factory=pd.DataFrame)
    missing_years: int = 0
    pval_df: dict = None
    cp_dict: dict = field(default_factory=dict)

    @property
    def ts(self):
        """Timeseries from data."""
        return self.data["peak_va"].values

    @property
    def nonstationary(self):
        # Update later
        return len(self.cp_dict) > 0

    @property
    def evidence_level(self):
        test_count = 0
        for cp in self.cp_dict:
            tmp = len(self.cp_dict[cp].split(","))
            test_count = max(test_count, tmp)
        if test_count == 0:
            return "no"
        elif test_count == 1:
            return "limited"
        elif test_count == 2:
            return "moderate"
        elif test_count > 2:
            return "strong"

    @property
    def summary_text(self):
        if self.nonstationary:
            end_text = """
            factors such as land use changes, climate change, or flow regulation (reservoirs,
            industrial processes, etc) may be influencing flow patterns at this site.
            """
        else:
            end_text = """an assumption of nonstationary conditions is likely reasonable."""
        if len(self.cp_dict) == 1:
            plural_text = "point was"
        else:
            plural_text = "points were"
        return (
            """
        There is **{}** evidence that the annual maximum series data at USGS gage {} are nonstationary in time. Four change
        point detection tests were completed to assess changes in the mean, variance, and overall distribution of flood
        peaks across the period of record. Significant change points were identified using a Type I error rate of 1 in
        {} and ignoring significant changes in the first and last {} years of data. {} statistically significant change
        {} identified, indicating that {}
        """
        ).format(
            self.evidence_level,
            st.session_state.gage_id,
            st.session_state.arlo_slider,
            st.session_state.burn_in,
            len(self.cp_dict),
            plural_text,
            end_text,
        )


def define_variables():
    """Set up page state and get default variables."""
    if "gage_id" not in st.session_state:
        st.session_state["gage_id"] = "12105900"
    if "changepoint" not in st.session_state:
        st.session_state.changepoint = ChangePointAnalysis(st.session_state["gage_id"])


def make_sidebar():
    """User control for analysis."""
    with st.sidebar:
        st.title("Settings")
        st.session_state["gage_id"] = st.text_input("Enter USGS Gage Number:", st.session_state["gage_id"])
        if len(st.session_state.changepoint.data) > 0:
            st.select_slider(
                "False Positive Rate (1 in #)",
                options=VALID_ARL0S,
                value=1000,
                key="arlo_slider",
                label_visibility="visible",
            )

            # max_burnin = floor(len(st.session_state.changepoint.data) / 2)
            st.number_input(
                "Burn-in Period",
                0,
                100,
                20,
                key="burn_in",
                label_visibility="visible",
            )
            st.text("Flood Frequency Analysis")
            init_data = pd.DataFrame({"Regime Start": [], "Regime End": []})
            st.data_editor(init_data, num_rows="dynamic", key="ffa_regimes")


@st.cache_data
def get_data(gage_id: int):
    print("getting data")
    return get_ams(gage_id)


def run_analysis():
    st.toast("Running change point analysis...")
    cpa = st.session_state.changepoint
    cpa.pval_df = get_pvalues(cpa.data)
    cpa.cp_dict = get_changepoints(cpa.data, st.session_state.arlo_slider, st.session_state.burn_in)
    return None


@st.cache_data
def get_pvalues(data: pd.DataFrame) -> pd.DataFrame:
    print("getting p values")
    ts = data["peak_va"].values
    pval_df = data[[]].copy()
    for metric in METRICS:
        pval_df[metric] = cp_pvalue_batch(metric, ts)
    return pval_df


@st.cache_data
def get_changepoints(data: pd.DataFrame, arl0: int, burn_in: int) -> dict:
    ts = data["peak_va"].values
    cp_dict = defaultdict(list)
    for metric in METRICS:
        stream_res = cpm_process_stream(ts, metric, arl0, burn_in)
        for cp in stream_res["changePoints"]:
            cp_dict[data.index[cp]].append(metric)
    for cp in cp_dict:
        cp_dict[cp] = ", ".join(cp_dict[cp])
    return cp_dict


def make_body():
    st.title(f"Changepoint Analysis for USGS Gage {st.session_state.gage_id}")
    warnings()
    cpa = st.session_state.changepoint
    if len(cpa.data) == 0:
        return
    st.header("Summary")
    st.markdown(cpa.summary_text)
    combo_plot = combo_cpm(cpa.data, cpa.pval_df, cpa.cp_dict)
    st.plotly_chart(combo_plot, use_container_width=True)
    st.header("Changepoint detection")
    st.markdown(
        test_description.format(st.session_state.arlo_slider, st.session_state.burn_in, st.session_state.burn_in)
    )
    if len(cpa.cp_dict) > 0:
        changepoint_table()
        st.text(references)
    # st.header("Modified flood frequency analysis")
    # st.markdown("Splitting the time series into windows of xyz, the resulting flood quantiles would be (plot).")

    word_data = format_as_word()
    st.download_button("Download analysis", word_data, f"changepoint_analysis_{st.session_state.gage_id}.docx")


def changepoint_table():
    cpa = st.session_state.changepoint
    cpa_df = pd.DataFrame.from_dict(cpa.cp_dict, orient="index", columns=["Tests Identifying Change"])
    st.table(cpa_df)
    st.text(
        "Table 1. Results of the changepoint analysis, listing dates when a significant change was identified for each test statistic."
    )


def warnings():
    """Print warnings on data validity etc."""
    if st.session_state.changepoint.data is not None and "peak_va" in st.session_state.changepoint.data.columns:
        if st.session_state.changepoint.missing_years:
            st.warning(
                f"Missing {len(st.session_state.changepoint.missing_years)} dates between {st.session_state.changepoint.data.index.min()} and {st.session_state.changepoint.data.index.max()}"
            )
    else:
        st.error("No peak flow data available.")


def format_as_word():
    document = Document()
    document.add_paragraph("Rollin on the river.")

    out = BytesIO()
    document.save(out)
    return out


def main():
    """Outline the page."""
    st.set_page_config(page_title="USGS Gage Changepoint Analysis", layout="wide")
    define_variables()
    make_sidebar()
    cpa = st.session_state.changepoint
    cpa.data, cpa.missing_years = get_data(st.session_state.gage_id)
    run_analysis()
    make_body()


if __name__ == "__main__":
    main()
