from collections import defaultdict
from dataclasses import dataclass, field
from math import floor

import pandas as pd
import streamlit as st
from data_retrieval import (
    get_ams,
)
from plots import combo_cpm, plot_ams, plot_cpm_heatmap

from tst.stats.tests import cp_pvalue_batch, cpm_process_stream

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


class ChangePointPage:

    ### Setup functions ###

    def __init__(self):
        """Set up page state and get default variables."""
        if "gage_no" not in st.session_state:
            st.session_state["gage_no"] = "testing"
        self.gage_no = st.session_state["gage_no"]

        if "changepoint" not in st.session_state:
            st.session_state["changepoint"] = {"arl0": 1000, "burn_in": 20, "evidence_level": "NA"}
        self.state = st.session_state["changepoint"]

        self.data, self.missing_years = None, None

        self.get_data()
        self.run_analysis()
        self.page()

    def page(self):
        """Make page body."""
        self.warnings()  # Warnings about data
        if self.data is None:
            return
        st.write(self.analysis_summary_text())  # Summary of analysis
        self.cpm_control()  # User control for change point model
        st.plotly_chart(self.cpm_plot(), use_container_width=True)  # Visual results of change point model
        st.write(self.cpm_text())  # Detailed description of change point model and results
        self.ffa_control()  # User control for flood frequency analysis (FFA)
        st.plotly_chart(self.ffa_plot(), use_container_width=True)  # Visual results of FFA
        self.ffa_table()  # Tabular results of FFA
        self.export_control()  # User control for data export

    ### Analysis functions ###

    @st.cache_data
    def get_data(self):
        """Get AMS data, validate, and display necessary warnings."""
        self.data, self.missing_years = get_ams(self.gage_no)

    @st.cache_data
    def run_analysis(self):
        """Run the changepoint model."""
        self.state.evidence_level = "Limited"
        self.state.evidence_level = "Moderate"
        self.state.evidence_level = "Strong"

    def analysis_summary_text(self):
        if self.state.nonstationary:
            end_text = """
            factors such as land use changes, climate change, or flow regulation (reservoirs,
            industrial processes, etc) may be influencing flow patterns at this site.
            """
        else:
            end_text = """an assumption of nonstationary conditions is likely reasonable."""
        return (
            """
        There is {} evidence that the {} data at USGS gage {} are nonstationary in time. Four change point detection
        tests were completed to assess changes in the mean, variance, and overall distribution of {} across the period
        of record. Significant change points were identified using a Type I error rate of 1 in {} and ignoring
        significant changes in the first and last {} {} of data. {} statistically significant change points were
        identified, indicating that
        """
            + end_text
        )

    def cpm_plot(self):
        """Make summary plot for change point model."""
        pass

    def cpm_text(self):
        """Text detailing change point model and results."""
        pass

    def ffa_plot(self):
        """Make summary plot for flood frequency analysis."""
        pass

    def ffa_table(self):
        """Make summary table for flood frequency analysis."""
        pass

    ### UI functions ###

    def cpm_control(self):
        """User control for change point model stream analysis tool."""
        col1, col2 = st.columns([1, 1])
        with col1:
            self.state.arl0 = st.select_slider(
                "False Positive Rate (1 in #)",
                options=self.VALID_ARL0S,
                value=self.state.arl0,
                key="arlo_slider",
                label_visibility="visible",
            )
        with col2:
            max_burnin = floor(len(self.data) / 2)
            self.state.burn_in = st.number_input(
                "Burn-in Period", 0, max_burnin, self.state.burn_in, key="num", label_visibility="visible"
            )

    def ffa_control(self):
        """User editable tabnle to control flood frequency analysis."""
        self.state.data_editor = st.data_editor()

    def export_control(self):
        """Allow user to save results."""
        st.download_button("Export analysis")


def changepoint_plot(gage_no: int, data: pd.DataFrame, arl0: int, burn_in: int):
    """Plot processed stream."""
    ts = data["peak_va"].values
    cp_dict = defaultdict(list)
    for metric in METRICS:
        stream_res = cpm_process_stream(ts, metric, arl0, burn_in)
        for cp in stream_res["changePoints"]:
            cp_dict[cp].append(metric)
    for cp in cp_dict:
        cp_dict[cp] = ", ".join(cp_dict[cp])
    st.plotly_chart(plot_ams(data, gage_no, cp_dict), use_container_width=True)


@st.cache_data
def pvalue_plot(data: pd.DataFrame):
    ts = data["peak_va"].values
    pval_df = data[[]]
    for metric in METRICS:
        pval_df[metric] = cp_pvalue_batch(metric, ts)
    st.plotly_chart(plot_cpm_heatmap(pval_df), use_container_width=True)


@dataclass
class ChangePointAnalysis:
    gage_id: int
    arl0: int = 1000
    burn_in: int = 20
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
        return (
            """
        There is **{}** evidence that the annual maximum series data at USGS gage {} are nonstationary in time. Four change
        point detection tests were completed to assess changes in the mean, variance, and overall distribution of flood
        peaks across the period of record. Significant change points were identified using a Type I error rate of 1 in
        {} and ignoring significant changes in the first and last {} years of data. {} statistically significant change
        point(s) were identified, indicating that {}
        """
        ).format(self.evidence_level, self.gage_id, self.arl0, self.burn_in, len(self.cp_dict), end_text)


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
            st.session_state.changepoint.arl0 = st.select_slider(
                "False Positive Rate (1 in #)",
                options=VALID_ARL0S,
                value=st.session_state.changepoint.arl0,
                key="arlo_slider",
                label_visibility="visible",
            )

            max_burnin = floor(len(st.session_state.changepoint.data) / 2)
            st.session_state.changepoint.burn_in = st.number_input(
                "Burn-in Period",
                0,
                max_burnin,
                st.session_state.changepoint.burn_in,
                key="num",
                label_visibility="visible",
            )


@st.cache_data
def get_data(gage_id: int):
    print("getting data")
    return get_ams(gage_id)


def run_analysis():
    st.toast("Running change point analysis...")
    cpa = st.session_state.changepoint
    cpa.pval_df = get_pvalues(cpa.data)
    cpa.cp_dict = get_changepoints(cpa.data, cpa.arl0, cpa.burn_in)
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
            cp_dict[cp].append(metric)
    for cp in cp_dict:
        cp_dict[cp] = ", ".join(cp_dict[cp])
    return cp_dict


def make_body():
    warnings()
    cpa = st.session_state.changepoint
    st.markdown(cpa.summary_text)
    st.plotly_chart(combo_cpm(cpa.data, cpa.pval_df, cpa.cp_dict), use_container_width=True)


def warnings():
    """Print warnings on data validity etc."""
    if st.session_state.changepoint.data is not None and "peak_va" in st.session_state.changepoint.data.columns:
        if st.session_state.changepoint.missing_years:
            st.warning(
                f"Missing {len(st.session_state.changepoint.missing_years)} dates between {st.session_state.changepoint.data.index.min()} and {st.session_state.changepoint.data.index.max()}"
            )
    else:
        st.error("No peak flow data available.")


def main():
    """Outline the page."""
    st.set_page_config(page_title="USGS Gage Changepoint Analysis", layout="wide")
    define_variables()
    cpa = st.session_state.changepoint
    gage_id = cpa.gage_id
    cpa.data, cpa.missing_years = get_data(gage_id)
    make_sidebar()
    run_analysis()
    make_body()

    # # Get data and validate
    # data = get_valid_data(gage_no)
    # if data is None:
    #     return

    # # Define analysis widgets

    # # Run analysis
    # run_analysis(arl0, burn_in)
    # changepoint_plot(gage_no, data, arl0, burn_in)

    # # Get pvalue plot
    # pvalue_plot(data)

    # analysis = analyze_ts(data)
    # st.plotly_chart(combo_cpm(data, gage_no, analysis["pval_df"], analysis["cps"]), use_container_width=True)

    # # Add a st.data_editor to let user define regime windows

    # # LPIII plot for different periods

    # # LPIII dataframe

    # # Export options


if __name__ == "__main__":
    main()
