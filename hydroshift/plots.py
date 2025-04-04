import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def plot_ams(ams_df, gage_id, cps: dict = {}):
    """Plots AMS (Annual Peak Flow) using Plotly with only markers (no line)."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=ams_df.index,
            y=ams_df["peak_va"],
            mode="markers",
            marker=dict(size=6, color="blue"),
            name="Peak Flow",
        )
    )
    if cps:
        for ind, cp in enumerate(cps):
            x = ams_df.index[cp]
            fig.add_trace(
                go.Scatter(
                    x=[x, x],
                    y=[ams_df["peak_va"].min(), ams_df["peak_va"].max()],
                    mode="lines",
                    line=dict(color="red", width=1, dash="dash"),
                    hovertext=[cps[cp], cps[cp]],
                    hoverinfo="text",
                    showlegend=False,
                )
            )
        # Label line
        fig.add_trace(
            go.Scatter(
                x=[0, 0],
                y=[0, 0],
                mode="lines",
                line=dict(color="red", width=1, dash="dash"),  # Dashed style
                hoverinfo="skip",  # Don't show hover on this trace
                showlegend=True,  # Hide the legend entry for this trace
                name="Statistically\nSignificant\nChangepoint",
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
    """Plots Flow Statistics using Plotly with correctly labeled legend entries."""
    # Ensure the data is sorted properly
    stats_df = stats_df.sort_values(by=["month_nu", "day_nu"])
    # Approximate day of year
    stats_df["day_of_year"] = stats_df["month_nu"] * 30 + stats_df["day_nu"]
    fig = go.Figure()
    # Add percentile shaded regions with correct labels
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p95_va"],
            mode="lines",
            line=dict(color="lightblue"),
            name="5th-95th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p05_va"],
            mode="lines",
            line=dict(color="lightblue"),
            fill="tonexty",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p90_va"],
            mode="lines",
            line=dict(color="blue"),
            name="10th-90th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p10_va"],
            mode="lines",
            line=dict(color="blue"),
            fill="tonexty",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p75_va"],
            mode="lines",
            line=dict(color="darkblue"),
            name="25th-75th Percentile",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["p25_va"],
            mode="lines",
            line=dict(color="darkblue"),
            fill="tonexty",
            showlegend=False,
        )
    )
    # Add mean flow
    fig.add_trace(
        go.Scatter(
            x=stats_df["day_of_year"],
            y=stats_df["mean_va"],
            mode="lines+markers",
            line=dict(color="black"),
            name="Mean Flow",
        )
    )
    fig.update_layout(
        title=f"{gage_id} | Daily Flow Statistics",
        xaxis_title="Day of Year",
        yaxis_title="Flow (cfs)",
        legend_title="Flow Statistics",
    )
    return fig


def plot_lp3(lp3_data: dict | list, gage_id: str, multi_series: bool = False):
    """Creates a Plotly chart for Log-Pearson Type III return period vs. peak flow."""
    # Convert dict to lists for plotting
    if not multi_series:
        ris = lp3_data
        lp3_data = {"Log-Pearson III Fit": ris}

    fig = go.Figure()

    for i in lp3_data:
        ris = lp3_data[i]
        return_periods = list(map(int, ris.keys()))
        peak_flows = list(ris.values())
        fig.add_trace(
            go.Scatter(
                x=return_periods,
                y=peak_flows,
                mode="markers+lines",
                marker=dict(size=8),
                line=dict(dash="solid"),
                name=i,
            )
        )
    fig.update_layout(
        title=f"{gage_id} | Log-Pearson Type III Estimates (No Regional Skew)",
        xaxis=dict(
            title="Return Period (years)",
            type="log",
            tickvals=return_periods,
            ticktext=[str(rp) for rp in return_periods],
        ),
        yaxis=dict(title="Peak Flow (cfs)"),
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
        color_discrete_map={"Winter": "blue", "Spring": "green", "Summer": "orange", "Fall": "brown"},
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
        go.Scatter(x=dv_df.index, y=dv_df["00060_Mean"], mode="lines", line=dict(color="blue"), name="Daily Mean Flow")
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


@st.cache_data
def combo_cpm(ams_df: pd.DataFrame, pval_df: pd.DataFrame, cps: dict = {}):
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
            x=ams_df.index, y=ams_df["peak_va"], mode="markers", marker=dict(size=6, color="blue"), name="Peak Flow"
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
    ).data[0]
    fig.add_trace(fig_imshow, row=2, col=1)

    # Update layout
    fig.update_layout(
        coloraxis=dict(colorscale=custom_color_scale, cmin=0.05, cmax=0.001),
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
        yaxis=dict(title="Peak Flow"),
        yaxis2=dict(title="Statistical Test"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=600,
    )

    return fig
