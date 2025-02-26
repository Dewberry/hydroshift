import plotly.express as px
import plotly.graph_objects as go


def plot_ams(ams_df, gage_id):
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
    # Update layout
    fig.update_layout(
        title=f"{gage_id} | Annual Peak Flow", xaxis_title="Date", yaxis_title="Peak Flow (cfs)", showlegend=True
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


def plot_lp3(lp3_data: dict, gage_id: str):
    """
    Creates a Plotly chart for Log-Pearson Type III return period vs. peak flow.
    """
    # Convert dict to lists for plotting
    return_periods = list(map(int, lp3_data.keys()))
    peak_flows = list(lp3_data.values())

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=return_periods,
            y=peak_flows,
            mode="markers+lines",
            marker=dict(color="blue", size=8),
            line=dict(color="blue", dash="solid"),
            name="Log-Pearson III Fit",
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
    """
    Creates a scatter plot for AMS ranked flow with seasons.
    """

    # Sort peak values and assign rank
    df = df.sort_values("peak_va").reset_index()
    df["rank"] = range(1, len(df) + 1)

    fig = px.scatter(
        df,
        x="rank",
        y="peak_va",
        color="season",
        title=f"Gage ID: {gage_id} | Flow Ranked from Low to High",
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
    """
    Creates a Plotly line plot for daily mean streamflow values.
    """
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
    """
    Creates a Plotly line plot for monthly mean streamflow values.
    """

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
