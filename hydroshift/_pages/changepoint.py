"""A tool to identify changepoints in hydrologic timeseries."""

from collections import defaultdict
from dataclasses import dataclass, field
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st
from data_retrieval import (
    get_ams,
)
from docx import Document
from docx.shared import Inches
from plotly import graph_objects
from plots import combo_cpm, plot_lp3

from hydroshift.consts import METRICS, VALID_ARL0S
from hydroshift.data_retrieval import log_pearson_iii
from hydroshift.stats.tests import cp_pvalue_batch, cpm_process_stream
from hydroshift.text.changepoint import references, test_description


@dataclass
class ChangePointAnalysis:
    """OOP representation of the changepoint analysis."""

    data: dict = field(default_factory=pd.DataFrame)
    missing_years: int = 0
    pval_df: dict = None
    cp_dict: dict = field(default_factory=dict)
    ffa_plot = None
    ffa_df: dict = field(default_factory=pd.DataFrame)

    @property
    def ts(self) -> np.ndarray:
        """Timeseries from data."""
        return self.data["peak_va"].values

    @property
    def nonstationary(self) -> bool:
        """Whether or not a nonstationarity was identified."""
        # Update later
        return len(self.cp_dict) > 0

    @property
    def evidence_level(self) -> str:
        """Text representation of how many tests identified changepoints."""
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

    def get_change_windows(self, max_dist: float = 10) -> tuple:
        """Find groups of cps that fall within a certain window of one another."""
        groups = []
        test_counts = []
        dates = list(self.cp_dict.keys())
        test_dict = {k: v.split(",") for k, v in self.cp_dict.items()}
        current_group = [dates[0]]
        current_group_tests = set(test_dict[dates[0]])

        for i in range(1, len(dates)):
            if ((dates[i] - current_group[-1]).days / 365) < max_dist:  # 10 years in days
                current_group.append(dates[i])
                current_group_tests = current_group_tests.union(test_dict[dates[i]])
            else:
                groups.append(current_group)
                test_counts.append(len(current_group_tests))
                current_group = [dates[i]]
                current_group_tests = set(test_dict[dates[i]])

        if current_group:
            groups.append(current_group)
            test_counts.append(len(current_group_tests))

        return groups, test_counts

    def get_max_pvalue(self):
        """Get the minimum p value where all tests agree and count how often that occurred."""
        all_tests = self.pval_df.fillna(1).max(axis=1).to_frame(name="pval")
        all_tests["run"] = ((all_tests != all_tests.shift(1)) * 1).cumsum()
        for ind, r in all_tests.groupby("pval").agg({"run": pd.Series.nunique}).sort_index().iterrows():
            if r.run > 0:
                min_p = ind
                count = r.run
                break
        return min_p, count

    def num_2_word(self, number: int) -> str:
        """Convert numbers less than 10 to words."""
        if number > 9:
            return number
        else:
            d = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
            return d[number]

    @property
    def summary_plot(self) -> graph_objects:
        """Create plotly plot to summarize analysis."""
        return combo_cpm(self.data, self.pval_df, self.cp_dict)

    @property
    @st.cache_resource
    def summary_png(self) -> BytesIO:
        """Export summary plot to png in memory."""
        bio = BytesIO()
        self.summary_plot.write_image(file=bio, width=1100, height=600)
        return bio

    @property
    def ffa_png(self):
        """Export FFA plot to png in memory."""
        bio = BytesIO()
        self.ffa_plot.write_image(file=bio, width=1100, height=600)
        return bio

    @property
    @st.cache_resource
    def cp_df(self):
        """Get a dataframe representing changepoints identified in the streaming analysis."""
        cpa_df = pd.DataFrame.from_dict(self.cp_dict, orient="index", columns=["Tests Identifying Change"])
        cpa_df.index = cpa_df.index.date
        return cpa_df

    @property
    def title(self) -> str:
        """Descriptive title of this analysis."""
        return f"Changepoint Analysis for USGS Gage {st.session_state.gage_id}"

    @property
    def summary_text(self) -> str:
        """A text summary of the changepoint analysis."""
        if self.nonstationary:
            end_text = """
            some form of nonstationarity (e.g., land use change, climate change, flow regulation, etc) may be influencing flow patterns at this site.
            """
        else:
            end_text = """an assumption of nonstationary conditions is likely reasonable."""
        cp_count = self.num_2_word(len(self.cp_dict))
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
            cp_count,
            plural_text,
            end_text,
        )

    @property
    def results_text(self) -> str:
        """A detailed description of the results."""
        # Static analysis
        min_p, p_count = self.get_max_pvalue()
        if min_p == 0.001:
            evidence = "strong"
        elif min_p == 0.005:
            evidence = "moderate"
        elif min_p < 1:
            evidence = "minor"
        else:
            evidence = "no"
        if p_count > 1:
            plural = "s"
        else:
            plural = ""
        p1 = """
            The static changepoint test showed {} evidence of a changepoint in the timeseries.  A minimum p-value of {}
            was obtained at {} contiguous time period{}.  The p-value reflects the probability that the distribution of
            flood peaks before that date has the **same** distribution as the flood peaks after the date.
        """.format(
            evidence, min_p, self.num_2_word(p_count), plural
        )

        # Streaming analysis
        if len(self.cp_dict) == 1:
            p2 = """
            The streaming analysis identified one statistically significant changepoint. This changepoint was identified
            by {} distinct tests: {}."""
        else:
            groups, test_counts = self.get_change_windows()
            if len(groups) > 0:
                plural = "s"
            else:
                plural = ""
            p2 = """
            The streaming analysis identified {} statistically significant changepoints. These changepoints broadly fell
            into {} window{} where tests identified changepoints not more than 10 years apart. For a full summary of which
            tests identified changes at which dates, see table 2.
            """.format(
                self.num_2_word(len(self.cp_dict)), self.num_2_word(len(groups)), plural
            )
        return "\n\n".join([p1, p2])

    @property
    def ffa_text(self) -> str:
        return """
                Based on the changepoint analysis results, a modified flood frequency analysis was conducted
                using truncated periods of record. The truncated periods correspond with times when the
                hydrologic regime appears to be stationary across time. Results from this analysis are shown
                in Figure 2 and Table 2.
                """

    @property
    def word_data(self) -> BytesIO:
        """Export text as MS word."""
        document = Document()
        document.add_heading(self.title, level=1)
        document.add_heading("Summary", level=2)
        self.add_markdown_to_doc(document, self.summary_text)
        document.add_picture(self.summary_png, width=Inches(6.5))
        document.add_heading("Changepoint detection method", level=2)
        self.add_markdown_to_doc(
            document,
            test_description.format(st.session_state.arlo_slider, st.session_state.burn_in, st.session_state.burn_in),
        )
        if len(self.cp_dict) > 0:
            document.add_heading("Changepoint detection results", level=2)
            self.add_markdown_to_doc(document, self.results_text)
            if len(self.cp_dict) > 1:
                self.add_table_from_df(self.cp_df, document, index_name="Date")

        if self.ffa_df is not None and self.ffa_plot is not None:
            document.add_heading("Modified flood frequency analysis", level=2)
            self.add_markdown_to_doc(document, self.ffa_text)
            document.add_picture(self.ffa_png, width=Inches(6.5))
            self.add_markdown_to_doc(document, "**Figure 2.** Modified flood frequency analysis.")
            self.add_markdown_to_doc(document, "**Table 2.** Modified flood quantiles.")
            self.add_table_from_df(self.ffa_df, document, index_name="Regime Period")

        document.add_heading("References", level=2)
        self.add_markdown_to_doc(document, references)

        out = BytesIO()
        document.save(out)
        return out

    def add_table_from_df(self, df: pd.DataFrame, document: Document, index_name: str = None):
        if index_name is not None:
            df = df.copy()
            cols = df.columns
            df[index_name] = df.index
            df = df[[index_name, *cols]]

        t = document.add_table(df.shape[0] + 1, df.shape[1])
        for j in range(df.shape[-1]):
            t.cell(0, j).text = df.columns[j]
        for i in range(df.shape[0]):
            for j in range(df.shape[-1]):
                t.cell(i + 1, j).text = str(df.values[i, j])
        t.style = "Light Grid"

    def add_markdown_to_doc(self, document: Document, text: str):
        """Convert some elements of markdown to word format."""
        text = text.replace("\n        ", "")
        p = document.add_paragraph("")
        bold = text.startswith("**")
        if bold:
            text = text[2:]
        for r in text.split("**"):
            p.add_run(r).bold = bold
            bold = not bold


def define_variables():
    """Set up page state and get default variables."""
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

            st.number_input(
                "Burn-in Period",
                0,
                100,
                20,
                key="burn_in",
                label_visibility="visible",
            )
            st.text("Flood Frequency Analysis")
            init_data = pd.DataFrame(columns=["Regime Start", "Regime End"])
            init_data["Regime Start"] = pd.to_datetime(init_data["Regime Start"])
            init_data["Regime End"] = pd.to_datetime(init_data["Regime End"])

            start_config = st.column_config.DateColumn("Regime Start", format="D/M/YYYY")
            end_config = st.column_config.DateColumn("Regime End", format="D/M/YYYY")
            st.data_editor(
                init_data,
                num_rows="dynamic",
                key="ffa_regimes",
                column_config={"Regime Start": start_config, "Regime End": end_config},
            )


@st.cache_data
def get_data(gage_id: int):
    """Cache results of get_ams."""
    return get_ams(gage_id)


def run_analysis():
    """Run the change point model analysis."""
    cpa = st.session_state.changepoint
    cpa.pval_df = get_pvalues(cpa.data)
    cpa.cp_dict = get_changepoints(cpa.data, st.session_state.arlo_slider, st.session_state.burn_in)
    return None


@st.cache_data
def get_pvalues(data: pd.DataFrame) -> pd.DataFrame:
    """Get pvalue df associated with changepoint analysis."""
    ts = data["peak_va"].values
    pval_df = data[[]].copy()
    for metric in METRICS:
        pval_df[metric] = cp_pvalue_batch(metric, ts)
    return pval_df


@st.cache_data
def get_changepoints(data: pd.DataFrame, arl0: int, burn_in: int) -> dict:
    """Run the process stream analysis and return changepoints identified."""
    ts = data["peak_va"].values
    cp_dict = defaultdict(list)
    for metric in METRICS:
        stream_res = cpm_process_stream(ts, metric, arl0, burn_in)
        for cp in stream_res["changePoints"]:
            cp_dict[data.index[cp]].append(metric)
    for cp in cp_dict:
        cp_dict[cp] = ", ".join(cp_dict[cp])
    return cp_dict


@st.cache_data
def ffa_analysis(data: pd.DataFrame, regimes: list):
    """Run multiple flood frequency analyses for different regimes."""
    ffa_dict = {}
    for r in regimes:
        if "Regime Start" in r and "Regime End" in r:
            sub = data.loc[r["Regime Start"] : r["Regime End"]]
            peaks = sub["peak_va"]
            lp3 = log_pearson_iii(peaks)
            label = f'{r["Regime Start"]} - {r["Regime End"]}'
            ffa_dict[label] = lp3
    if len(ffa_dict) > 0:
        ffa_plot = plot_lp3(ffa_dict, st.session_state.gage_id, multi_series=True)

        ffa_df = pd.DataFrame.from_dict(ffa_dict, orient="index")
        renames = {c: f"Q{c}" for c in ffa_df.columns}
        ffa_df = ffa_df.rename(columns=renames)
        return ffa_plot, ffa_df
    else:
        return None, None


def make_body():
    """Assemble main app body."""
    left_col, right_col = st.columns([2, 1])  # Formatting
    with left_col:
        cpa = st.session_state.changepoint
        st.title(cpa.title)
        warnings()
        if len(cpa.data) == 0:
            return

        st.header("Summary")
        st.markdown(cpa.summary_text)
        st.plotly_chart(cpa.summary_plot, use_container_width=True)
        st.markdown("**Figure 1.** Statistical changepoint analysis.")
        st.header("Changepoint detection method")
        st.markdown(
            test_description.format(st.session_state.arlo_slider, st.session_state.burn_in, st.session_state.burn_in)
        )

        if len(cpa.cp_dict) > 0:
            st.header("Changepoint detection results")
            st.markdown(cpa.results_text)
            if len(cpa.cp_dict) > 1:
                st.table(cpa.cp_df)
                st.markdown(
                    "**Table 1.** Results of the changepoint analysis, listing dates when a significant change was identified for each test statistic."
                )

        st.header("Modified flood frequency analysis")
        if len(st.session_state.ffa_regimes["added_rows"]) > 0:
            ffa_plot, ffa_df = ffa_analysis(cpa.data, st.session_state.ffa_regimes["added_rows"])
            if ffa_plot is not None and ffa_df is not None:
                st.markdown(cpa.ffa_text)
                cpa.ffa_plot = ffa_plot
                cpa.ffa_df = ffa_df
                st.plotly_chart(ffa_plot, use_container_width=True)
                st.markdown("**Figure 2.** Modified flood frequency analysis.")
                st.markdown("**Table 2.** Modified flood quantiles.")
                st.table(ffa_df)
        else:
            st.info(
                "To run pre- and post-changepoint flood frequency analyses, you can input timeseries ranges (regimes) in the flood frequency table on the sidebar.  You may add as many regimes as you think are appropriate, and the periods may overlap."
            )

        st.header("References")
        st.markdown(references)

        st.download_button("Download analysis", cpa.word_data, f"changepoint_analysis_{st.session_state.gage_id}.docx")


def warnings():
    """Print warnings on data validity etc."""
    if st.session_state.changepoint.data is not None and "peak_va" in st.session_state.changepoint.data.columns:
        if st.session_state.changepoint.missing_years:
            st.warning(
                f"Missing {len(st.session_state.changepoint.missing_years)} dates between {st.session_state.changepoint.data.index.min()} and {st.session_state.changepoint.data.index.max()}"
            )
    else:
        st.error("No peak flow data available.")


def changepoint():
    """Outline the page."""
    st.set_page_config(page_title="USGS Gage Changepoint Analysis", layout="wide")
    define_variables()
    make_sidebar()
    cpa = st.session_state.changepoint
    cpa.data, cpa.missing_years = get_data(st.session_state.gage_id)
    run_analysis()
    make_body()
