"""Plotly-based interactive charts for the Streamlit UI."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def distributions(df: pd.DataFrame) -> go.Figure:
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        return None

    cols = min(len(num_cols), 3)
    rows = (len(num_cols) + cols - 1) // cols
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=num_cols)

    for i, col in enumerate(num_cols):
        r, c = divmod(i, cols)
        fig.add_trace(
            go.Histogram(x=df[col].dropna(), name=col, showlegend=False,
                         marker_color="#636EFA"),
            row=r + 1, col=c + 1,
        )

    fig.update_layout(title="Numeric Distributions", height=300 * rows,
                      template="plotly_white")
    return fig


def correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    num_df = df.select_dtypes(include="number")
    if num_df.shape[1] < 2:
        return None

    corr = num_df.corr().round(3)
    fig = px.imshow(
        corr, text_auto=True, color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1, title="Correlation Heatmap",
    )
    fig.update_layout(template="plotly_white")
    return fig


def top_categories(df: pd.DataFrame, col: str, top_n: int = 10) -> go.Figure:
    counts = df[col].value_counts().head(top_n).reset_index()
    counts.columns = [col, "count"]
    fig = px.bar(counts, x="count", y=col, orientation="h",
                 title=f"Top {top_n}: {col}", template="plotly_white",
                 color="count", color_continuous_scale="Blues")
    fig.update_layout(yaxis={"categoryorder": "total ascending"},
                      coloraxis_showscale=False)
    return fig


def monthly_trend(df: pd.DataFrame, date_col: str, value_col: str) -> go.Figure:
    temp = df[[date_col, value_col]].copy()
    temp["month"] = temp[date_col].dt.to_period("M").astype(str)
    monthly = temp.groupby("month")[value_col].sum().reset_index()
    fig = px.line(monthly, x="month", y=value_col, markers=True,
                  title=f"Monthly Trend: {value_col}", template="plotly_white")
    fig.update_layout(xaxis_title="Month")
    return fig


def group_comparison(df: pd.DataFrame, group_col: str, value_col: str) -> go.Figure:
    grouped = (df.groupby(group_col)[value_col]
               .sum().sort_values(ascending=False).reset_index())
    fig = px.bar(grouped, x=group_col, y=value_col,
                 title=f"{value_col} by {group_col}", template="plotly_white",
                 color=value_col, color_continuous_scale="Blues")
    fig.update_layout(coloraxis_showscale=False)
    return fig


def boxplots(df: pd.DataFrame) -> go.Figure:
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        return None

    fig = go.Figure()
    for col in num_cols:
        fig.add_trace(go.Box(y=df[col].dropna(), name=col, boxpoints="outliers"))
    fig.update_layout(title="Boxplots (Outlier View)", template="plotly_white",
                      showlegend=False)
    return fig


def missing_values(df: pd.DataFrame) -> go.Figure:
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=True)
    if missing.empty:
        return None

    fig = px.bar(x=missing.values, y=missing.index, orientation="h",
                 title="Missing Values per Column", template="plotly_white",
                 labels={"x": "Missing Count", "y": "Column"})
    return fig
