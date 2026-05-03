import pandas as pd


def overview(df: pd.DataFrame) -> dict:
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing": df.isnull().sum().to_dict(),
        "missing_pct": (df.isnull().mean() * 100).round(2).to_dict(),
        "duplicates": int(df.duplicated().sum()),
    }


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    return df.describe().round(2)


def top_values(df: pd.DataFrame, top_n: int = 5) -> dict:
    result = {}
    for col in df.select_dtypes(include=["object", "category"]).columns:
        counts = df[col].value_counts().head(top_n)
        result[col] = counts.to_dict()
    return result


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    num_df = df.select_dtypes(include="number")
    if num_df.shape[1] < 2:
        return pd.DataFrame()
    return num_df.corr().round(3)


def monthly_trend(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    if date_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    temp = df[[date_col, value_col]].copy()
    temp["month"] = temp[date_col].dt.to_period("M")
    return temp.groupby("month")[value_col].sum().reset_index()


def group_summary(df: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
    if group_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(group_col)[value_col]
        .agg(["sum", "mean", "count"])
        .round(2)
        .sort_values("sum", ascending=False)
        .rename(columns={"sum": "total", "mean": "average", "count": "transactions"})
    )


def outliers(df: pd.DataFrame) -> dict:
    result = {}
    for col in df.select_dtypes(include="number").columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        count = int(((df[col] < low) | (df[col] > high)).sum())
        if count > 0:
            result[col] = {"outlier_count": count, "lower_bound": round(low, 2), "upper_bound": round(high, 2)}
    return result
