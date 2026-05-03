"""Streamlit web UI for the CSV Data Analyzer."""

import io
import pandas as pd
import streamlit as st

from analyzer.loader import load_csv
from analyzer import insights
from analyzer import charts

st.set_page_config(
    page_title="CSV Data Analyzer",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 CSV Analyzer")
    st.markdown("Upload any CSV file to get instant insights and interactive charts.")

    uploaded = st.file_uploader("Drop your CSV here", type=["csv"],
                                label_visibility="collapsed")

    st.divider()
    st.markdown("**Settings**")
    top_n = st.slider("Top N categories to show", 3, 20, 10)

    st.divider()
    st.caption("Built with Streamlit · [GitHub](https://github.com/namlecanh/csv-analyzer)")


# ── Load data ─────────────────────────────────────────────────────────────────

@st.cache_data
def load_data(file_bytes: bytes, filename: str) -> pd.DataFrame:
    return load_csv(io.BytesIO(file_bytes), filename)


# Patch loader to also accept file-like objects
import pandas as _pd
from pathlib import Path as _Path


def load_csv_ui(source, filename: str = "") -> pd.DataFrame:
    if isinstance(source, (str, _Path)):
        df = _pd.read_csv(source)
    else:
        df = _pd.read_csv(source)

    for col in df.columns:
        if "date" in col.lower():
            df[col] = _pd.to_datetime(df[col], errors="coerce")
    return df


# ── Main area ─────────────────────────────────────────────────────────────────

if uploaded is None:
    st.markdown("## Welcome to CSV Data Analyzer")
    st.markdown(
        "Upload a CSV file using the sidebar to explore your data — "
        "statistics, trends, correlations, and charts are generated automatically."
    )

    with st.expander("Try the sample dataset"):
        if st.button("Load sample_sales.csv"):
            with open("data/sample_sales.csv", "rb") as f:
                st.session_state["sample"] = f.read()

    if "sample" in st.session_state:
        df = load_csv_ui(io.BytesIO(st.session_state["sample"]))
    else:
        st.stop()
else:
    df = load_csv_ui(io.BytesIO(uploaded.read()), uploaded.name)

# ── Auto-detect key columns ────────────────────────────────────────────────────

num_cols = df.select_dtypes(include="number").columns.tolist()
cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

date_col = date_cols[0] if date_cols else None

value_col = next(
    (c for c in num_cols
     if any(k in c.lower() for k in ["revenue", "profit", "sales", "amount", "total", "value"])),
    num_cols[-1] if num_cols else None,
)

group_col = next(
    (c for c in cat_cols
     if any(k in c.lower() for k in ["region", "category", "product", "department", "segment"])),
    cat_cols[0] if cat_cols else None,
)

# ── File header ───────────────────────────────────────────────────────────────

filename = uploaded.name if uploaded else "sample_sales.csv"
st.markdown(f"## {filename}")

info = insights.overview(df)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rows", f"{info['rows']:,}")
col2.metric("Columns", info["columns"])
col3.metric("Missing Values", sum(info["missing"].values()))
col4.metric("Duplicates", info["duplicates"])

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_overview, tab_stats, tab_charts, tab_data = st.tabs(
    ["Overview", "Statistics", "Charts", "Raw Data"]
)

# ── Tab: Overview ─────────────────────────────────────────────────────────────

with tab_overview:
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Column Info")
        dtype_df = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.notnull().sum().values,
            "Missing": df.isnull().sum().values,
            "Missing %": (df.isnull().mean() * 100).round(1).values,
        })
        st.dataframe(dtype_df, use_container_width=True, hide_index=True)

    with col_r:
        missing_fig = charts.missing_values(df)
        if missing_fig:
            st.subheader("Missing Values")
            st.plotly_chart(missing_fig, use_container_width=True)
        else:
            st.success("No missing values in this dataset.")

        if info["duplicates"] > 0:
            st.warning(f"{info['duplicates']} duplicate rows detected.")


# ── Tab: Statistics ───────────────────────────────────────────────────────────

with tab_stats:
    st.subheader("Numeric Summary")
    summary = insights.numeric_summary(df)
    if not summary.empty:
        st.dataframe(summary, use_container_width=True)

    st.subheader("Outliers (IQR Method)")
    outs = insights.outliers(df)
    if outs:
        out_df = pd.DataFrame([
            {"Column": col, "Outlier Count": v["outlier_count"],
             "Lower Bound": v["lower_bound"], "Upper Bound": v["upper_bound"]}
            for col, v in outs.items()
        ])
        st.dataframe(out_df, use_container_width=True, hide_index=True)
    else:
        st.success("No outliers detected.")

    if group_col and value_col:
        st.subheader(f"{value_col.title()} by {group_col.title()}")
        group_df = insights.group_summary(df, group_col, value_col)
        st.dataframe(group_df, use_container_width=True)

    if date_col and value_col:
        st.subheader(f"Monthly Trend: {value_col.title()}")
        trend_df = insights.monthly_trend(df, date_col, value_col)
        st.dataframe(trend_df, use_container_width=True, hide_index=True)


# ── Tab: Charts ───────────────────────────────────────────────────────────────

with tab_charts:

    # Distributions
    st.subheader("Distributions")
    dist_fig = charts.distributions(df)
    if dist_fig:
        st.plotly_chart(dist_fig, use_container_width=True)

    # Correlation heatmap
    st.subheader("Correlation Heatmap")
    corr_fig = charts.correlation_heatmap(df)
    if corr_fig:
        st.plotly_chart(corr_fig, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns for a correlation heatmap.")

    # Boxplots
    st.subheader("Boxplots")
    box_fig = charts.boxplots(df)
    if box_fig:
        st.plotly_chart(box_fig, use_container_width=True)

    # Monthly trend
    if date_col and value_col:
        st.subheader(f"Monthly Trend: {value_col.title()}")
        trend_fig = charts.monthly_trend(df, date_col, value_col)
        st.plotly_chart(trend_fig, use_container_width=True)

    # Group comparison
    if group_col and value_col:
        st.subheader(f"{value_col.title()} by Group")
        c1, c2 = st.columns(2)
        with c1:
            sel_group = st.selectbox("Group by", cat_cols, index=cat_cols.index(group_col))
        with c2:
            sel_value = st.selectbox("Measure", num_cols, index=num_cols.index(value_col))
        group_fig = charts.group_comparison(df, sel_group, sel_value)
        st.plotly_chart(group_fig, use_container_width=True)

    # Top categories
    if cat_cols:
        st.subheader("Category Breakdown")
        sel_cat = st.selectbox("Select column", cat_cols)
        cat_fig = charts.top_categories(df, sel_cat, top_n)
        st.plotly_chart(cat_fig, use_container_width=True)


# ── Tab: Raw Data ─────────────────────────────────────────────────────────────

with tab_data:
    st.subheader("Raw Data")

    search = st.text_input("Filter rows (searches all columns)", "")
    if search:
        mask = df.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
        filtered = df[mask]
        st.caption(f"{len(filtered):,} of {len(df):,} rows match")
    else:
        filtered = df

    st.dataframe(filtered, use_container_width=True, height=500)

    csv_bytes = filtered.to_csv(index=False).encode()
    st.download_button("Download filtered CSV", csv_bytes,
                       file_name="filtered_data.csv", mime="text/csv")
