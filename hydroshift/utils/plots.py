import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots
from scipy.stats import norm

from hydroshift.consts import MAX_CACHE_ENTRIES
from hydroshift.utils.common import classify_regulation
from hydroshift.utils.ffa import LP3Analysis


def plot_ams(ams_df, gage_id, cps: dict = {}):
    """Plot AMS (Annual Peak Flow) with markers colored by regulation status."""
    fig = go.Figure()

    # Classify each point as regulated or not
    ams_df["regulated"] = ams_df["peak_cd"].apply(classify_regulation)

    # Plot non-regulated points
    fig.add_trace(
        go.Scatter(
            x=ams_df[~ams_df["regulated"]].index,
            y=ams_df[~ams_df["regulated"]]["peak_va"],
            mode="markers",
            marker=dict(size=6, color="blue"),
            name="Non-Regulated",
        )
    )

    # Plot regulated points
    fig.add_trace(
        go.Scatter(
            x=ams_df[ams_df["regulated"]].index,
            y=ams_df[ams_df["regulated"]]["peak_va"],
            mode="markers",
            marker=dict(size=6, color="red"),
            name="Regulated",
        )
    )

    # Plot changepoints if provided
    if cps:
        for ind, cp in enumerate(cps):
            x = ams_df.index[cp]
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[ams_df["peak_va"].min(), ams_df["peak_va"].max()],
                    mode="lines",
                    line=dict(color="black", width=1, dash="dash"),
                    hovertext=[cps[cp], cps[cp]],
                    hoverinfo="text",
                    showlegend=False,
                )
            )
        # Legend label for changepoint
        fig.add_trace(
            go.Scatter(
                x=[0, 0],
                y=[0, 0],
                mode="lines",
                line=dict(color="black", width=1, dash="dash"),
                hoverinfo="skip",
                showlegend=True,
                name="Statistically Significant Changepoint",
            )
        )

    # Update layout
    fig.update_layout(
        title=f"{gage_id} | Annual Peak Flow",
        xaxis_title="Date",
        yaxis_title="Peak Flow (cfs)",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.99,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def plot_flow_stats(stats_df, gage_id):
    """Plot Flow Statistics using Plotly with month-abbreviation x-axis labels."""
    # Ensure data is sorted
    # Create a datetime column
    p_cols = ["p05_va", "p10_va", "p20_va", "p25_va", "p50_va", "p75_va", "p80_va", "p90_va", "p95_va"]
    stats_df[p_cols] = stats_df[p_cols].ffill()
    stats_df[p_cols] = stats_df[p_cols].fillna(0)
    stats_df["date"] = pd.to_datetime(
        {
            "year": 2000,  # dummy leap year to support Feb 29
            "month": stats_df["month_nu"],
            "day": stats_df["day_nu"],
        },
        errors="coerce",
    )
    stats_df = stats_df.sort_values(by=["month_nu", "day_nu"])
    # Approximate day of year
    stats_df["day_of_year"] = stats_df["month_nu"] * 30 + stats_df["day_nu"]
    fig = go.Figure()
    # Percentile bands

    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p95_va"],
            mode="lines",
            line=dict(color="lightblue"),
            name="5th-95th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p05_va"],
            mode="lines",
            line=dict(color="lightblue"),
            fill="tonexty",
            showlegend=False,
            name="5th-95th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p90_va"],
            mode="lines",
            line=dict(color="blue"),
            name="10th-90th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p10_va"],
            mode="lines",
            line=dict(color="blue"),
            fill="tonexty",
            showlegend=False,
            name="10th-90th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p75_va"],
            mode="lines",
            line=dict(color="darkblue"),
            name="25th-75th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["p25_va"],
            mode="lines",
            line=dict(color="darkblue"),
            fill="tonexty",
            showlegend=False,
            name="25th-75th Percentile",
        )
    )

    # Mean flow line
    fig.add_trace(
        go.Scatter(
            x=stats_df["date"],
            y=stats_df["mean_va"],
            mode="lines+markers",
            line=dict(color="black"),
            name="Mean Flow",
        )
    )

    # Format layout with month abbreviations
    fig.update_layout(
        title=f"{gage_id} | Daily Flow Statistics",
        xaxis_title="Month",
        yaxis_title="Flow (cfs)",
        legend_title="Flow Statistics",
        xaxis=dict(
            tickformat="%b",  # abbreviated month name
            dtick="M1",  # monthly ticks
        ),
    )
    return fig


def plot_lp3(data: LP3Analysis | list[LP3Analysis]):
    """Creates a Plotly chart for Log-Pearson Type III return period vs. peak flow."""
    # Convert dict to lists for plotting
    if isinstance(data, LP3Analysis):
        data = [data]

    fig = go.Figure()

    for i in data:
        name = i.label + " - Peaks"
        aep, peaks = i.plotting_positions
        z = norm.ppf(1 - aep)
        fig.add_trace(
            go.Scatter(
                x=z,
                y=peaks,
                mode="markers",
                marker=dict(size=8, symbol="circle-open"),
                name=name,
            )
        )

        name = i.label + " - Log-Pearson III Fit"
        aep2, peaks2 = i.ffa_quantiles
        z2 = norm.ppf(1 - aep2)
        fig.add_trace(
            go.Scatter(
                x=z2,
                y=peaks2,
                mode="markers+lines",
                marker=dict(size=8),
                line=dict(dash="solid"),
                name=name,
            )
        )

    # Formatting
    return_periods = [int(i) if i.is_integer() else round(i, 1) for i in i.return_periods]
    skew_txt = f" ({i.skew_mode})"
    fig.update_layout(
        title=f"{i.gage_id} | Log-Pearson Type III Estimates{skew_txt}",
        xaxis=dict(
            title="Return Period (years)",
            tickvals=z2,
            ticktext=return_periods,
        ),
        yaxis=dict(title="Peak Flow (cfs)", type="log"),
        showlegend=True,
        template="plotly_white",
    )

    return fig


def plot_ams_seasonal(df, gage_id):
    """Creates a scatter plot for AMS ranked flow with seasons."""
    # Sort peak values and assign rank
    df = df.sort_values("peak_va").reset_index()
    df["rank"] = range(1, len(df) + 1)

    fig = px.scatter(
        df,
        x="rank",
        y="peak_va",
        color="season",
        title=f"Gage ID: {gage_id} | Seasonal AMS Ranked from Low to High",
        labels={"rank": "Rank", "peak_va": "Flow (cfs)"},
        color_discrete_map={
            "Winter": "blue",
            "Spring": "green",
            "Summer": "orange",
            "Fall": "brown",
        },
    )

    fig.update_layout(
        legend_title="Season",
        template="plotly_white",
        xaxis=dict(title="Rank (Low to High Flow)"),
        yaxis=dict(title="Peak Flow (cfs)"),
    )

    return fig


def plot_daily_mean(dv_df, gage_id):
    """Creates a Plotly line plot for daily mean streamflow values."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dv_df.index,
            y=dv_df["00060_Mean"],
            mode="lines",
            line=dict(color="blue"),
            name="Daily Mean Flow",
        )
    )

    fig.update_layout(
        title=f"{gage_id} | Daily Mean Streamflow",
        xaxis_title="Date",
        yaxis_title="Flow (cfs)",
        showlegend=True,
        template="plotly_white",
    )

    return fig


def plot_monthly_mean(monthly_df, gage_id):
    """Creates a Plotly line plot for monthly mean streamflow values."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_df["date"],
            y=monthly_df["mean_va"],
            mode="lines",
            line=dict(color="blue"),
            name="Monthly Mean Flow",
        )
    )
    fig.update_layout(
        title=f"{gage_id} | Monthly Mean Streamflow",
        xaxis_title="Date",
        yaxis_title="Flow (cfs)",
        showlegend=True,
        template="plotly_white",
    )

    return fig


def plot_cpm_heatmap(pval_df: pd.DataFrame):
    """Plot a heatmap of changepoint p values."""
    custom_color_scale = [
        (0, "#f52e20"),  # Red
        (0.33, "#eb9f34"),  # Orange
        (0.66, "#f7ef52"),  # Yellow
        (1.0, "#f5f2b8"),  # Cream
    ]

    fig = px.imshow(
        pval_df.T,
        color_continuous_scale=custom_color_scale,
        labels=dict(x="Date", y="Statistical Test", color="P-Value"),
        range_color=[0.05, 0.001],
        height=75 * len(pval_df.columns),
        title="Changepoint Analysis",
    )

    # fig.update_coloraxes(
    #     showscale=True,
    #     colorbar={
    #         "orientation": "h",
    #         "yanchor": "bottom",
    #         "y": -0.75,
    #         "xanchor": "left",
    #         "x": 0.01,
    #     },
    # )

    # # Update layout
    # fig.update_layout(
    #     title=f"{gage_id} | Changepoint Analysis",
    #     # showlegend=True,
    #     # legend=dict(
    #     #     orientation="h",
    #     #     yanchor="bottom",
    #     #     y=0.01,
    #     #     xanchor="center",
    #     #     x=0.5,
    #     # ),
    # )
    return fig


@st.cache_data(max_entries=MAX_CACHE_ENTRIES)
def combo_cpm(ams_df: pd.DataFrame, pval_df: pd.DataFrame, cps: dict = {}) -> Figure:
    """Plot a change point model with peak flows and statistical analysis."""
    # Create subplots
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[2, 1],
        shared_xaxes=True,
        vertical_spacing=0.05,
    )
    # Scatter plot for peak flow data
    fig.add_trace(
        go.Scatter(
            x=ams_df.index,
            y=ams_df["peak_va"],
            mode="markers",
            marker=dict(size=6, color="blue"),
            name="Peak Flow",
        ),
        row=1,
        col=1,
    )

    # Add changepoint lines
    for cp, label in cps.items():
        # x = ams_df.index[cp]
        fig.add_trace(
            go.Scatter(
                x=[cp, cp],
                y=[ams_df["peak_va"].min(), ams_df["peak_va"].max()],
                mode="lines",
                line=dict(color="red", width=1, dash="dash"),
                hovertext=[label, label],
                hoverinfo="text",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

    # Legend entry for changepoint lines
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],  # Invisible point for legend
            mode="lines",
            line=dict(color="red", width=1, dash="dash"),
            name="Statistically\nSignificant\nChangepoint",
        )
    )

    # Custom color scale for p-values
    custom_color_scale = [
        (0, "#f52e20"),  # Red
        (0.33, "#eb9f34"),  # Orange
        (0.66, "#f7ef52"),  # Yellow
        (1.0, "#f5f2b8"),  # Cream
    ]

    fig_imshow = px.imshow(
        pval_df.T,
        color_continuous_scale=custom_color_scale,
        labels=dict(x="Date", y="Statistical Test", color="P-Value"),
        title="Changepoint Analysis",
        zmin=0.001,
        zmax=0.05,
    ).data[0]
    fig.add_trace(fig_imshow, row=2, col=1)

    # Update layout
    fig.update_layout(
        coloraxis=dict(colorscale=custom_color_scale, cmax=0.05, cmin=0.001),
        coloraxis_colorbar=dict(
            orientation="h",
            yanchor="bottom",
            y=0.96,
            xanchor="right",
            x=0.94,
            len=0.3,
            thickness=0.5,
            xpad=0,
            ypad=0,
            title=dict(side="top", text="P-Value"),
            tickvals=[0.05, 0.001],
            ticktext=["0.05", "0.001"],
        ),
        legend_tracegroupgap=10,
        xaxis2=dict(title="Date"),
        yaxis=dict(title="Peak Flow (cfs)"),
        yaxis2=dict(title="Statistical Test"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=600,
    )

    return fig
