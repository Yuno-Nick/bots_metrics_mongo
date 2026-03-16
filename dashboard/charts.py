"""Plotly chart helper functions for the AI Agent Analytics dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=40, b=40),
    font=dict(size=12),
)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
) -> go.Figure:
    fig = px.line(df, x=x, y=y, title=title, color=color, markers=True)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    horizontal: bool = False,
    color: str | None = None,
) -> go.Figure:
    if horizontal:
        fig = px.bar(df, x=y, y=x, title=title, orientation="h", color=color)
    else:
        fig = px.bar(df, x=x, y=y, title=title, color=color)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str,
) -> go.Figure:
    fig = px.pie(df, names=names, values=values, title=title, hole=0.4)
    fig.update_layout(**_LAYOUT_DEFAULTS)
    return fig


def stacked_bar(
    df: pd.DataFrame,
    x: str,
    y_cols: list[str],
    title: str,
) -> go.Figure:
    fig = go.Figure()
    for col in y_cols:
        fig.add_trace(go.Bar(name=col, x=df[x], y=df[col]))
    fig.update_layout(barmode="stack", title=title, **_LAYOUT_DEFAULTS)
    return fig


def format_cost(value: float) -> str:
    """Format a numeric value as USD."""
    if value >= 1:
        return f"${value:,.2f}"
    return f"${value:,.4f}"
