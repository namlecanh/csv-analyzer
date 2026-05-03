import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_theme(style="whitegrid", palette="muted")


def _save(fig, output_dir: Path, filename: str) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return str(path)


def plot_distributions(df: pd.DataFrame, output_dir: Path) -> list[str]:
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        return []

    cols = min(len(num_cols), 3)
    rows = (len(num_cols) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4))
    axes = [axes] if rows * cols == 1 else axes.flatten()

    for i, col in enumerate(num_cols):
        sns.histplot(df[col].dropna(), kde=True, ax=axes[i])
        axes[i].set_title(f"Distribution: {col}")
        axes[i].set_xlabel(col)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle("Numeric Column Distributions", fontsize=14, y=1.01)
    return [_save(fig, output_dir, "distributions.png")]


def plot_correlation_heatmap(df: pd.DataFrame, output_dir: Path) -> list[str]:
    num_df = df.select_dtypes(include="number")
    if num_df.shape[1] < 2:
        return []

    corr = num_df.corr()
    fig, ax = plt.subplots(figsize=(max(6, len(corr) * 1.2), max(5, len(corr))))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
    ax.set_title("Correlation Heatmap")
    return [_save(fig, output_dir, "correlation_heatmap.png")]


def plot_top_categories(df: pd.DataFrame, output_dir: Path, top_n: int = 5) -> list[str]:
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if not cat_cols:
        return []

    saved = []
    for col in cat_cols[:4]:  # limit to 4 categorical columns
        counts = df[col].value_counts().head(top_n)
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x=counts.values, y=counts.index, ax=ax, hue=counts.index, palette="muted", legend=False)
        ax.set_title(f"Top {top_n}: {col}")
        ax.set_xlabel("Count")
        saved.append(_save(fig, output_dir, f"top_{col.lower().replace(' ', '_')}.png"))

    return saved


def plot_monthly_trend(df: pd.DataFrame, date_col: str, value_col: str, output_dir: Path) -> list[str]:
    if date_col not in df.columns or value_col not in df.columns:
        return []

    temp = df[[date_col, value_col]].copy()
    temp["month"] = temp[date_col].dt.to_period("M").astype(str)
    monthly = temp.groupby("month")[value_col].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.lineplot(data=monthly, x="month", y=value_col, marker="o", ax=ax)
    ax.set_title(f"Monthly Trend: {value_col}")
    ax.set_xlabel("Month")
    ax.tick_params(axis="x", rotation=45)
    return [_save(fig, output_dir, f"trend_{value_col.lower().replace(' ', '_')}.png")]


def plot_group_comparison(df: pd.DataFrame, group_col: str, value_col: str, output_dir: Path) -> list[str]:
    if group_col not in df.columns or value_col not in df.columns:
        return []

    grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.barplot(x=grouped.index, y=grouped.values, ax=ax, hue=grouped.index, palette="muted", legend=False)
    ax.set_title(f"{value_col} by {group_col}")
    ax.set_xlabel(group_col)
    ax.set_ylabel(f"Total {value_col}")
    ax.tick_params(axis="x", rotation=30)
    return [_save(fig, output_dir, f"group_{group_col.lower()}_{value_col.lower()}.png")]
