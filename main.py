#!/usr/bin/env python3
"""CSV Data Analyzer — load any CSV and get instant insights + charts."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from analyzer.loader import load_csv
from analyzer import insights, visualizer

console = Console()


def print_overview(info: dict):
    console.print(Panel.fit("[bold cyan]Dataset Overview[/bold cyan]"))
    table = Table(box=box.SIMPLE)
    table.add_column("Property", style="bold")
    table.add_column("Value")
    table.add_row("Rows", str(info["rows"]))
    table.add_row("Columns", str(info["columns"]))
    table.add_row("Duplicates", str(info["duplicates"]))
    table.add_row("Columns", ", ".join(info["column_names"]))
    console.print(table)

    missing = {k: v for k, v in info["missing"].items() if v > 0}
    if missing:
        console.print("\n[yellow]Missing Values:[/yellow]")
        for col, count in missing.items():
            pct = info["missing_pct"][col]
            console.print(f"  {col}: {count} ({pct}%)")
    else:
        console.print("[green]No missing values.[/green]")


def print_numeric_summary(df):
    summary = insights.numeric_summary(df)
    if summary.empty:
        return
    console.print(Panel.fit("[bold cyan]Numeric Summary[/bold cyan]"))
    table = Table(box=box.SIMPLE)
    table.add_column("Stat", style="bold")
    for col in summary.columns:
        table.add_column(col)
    for stat in summary.index:
        row = [stat] + [str(summary.loc[stat, col]) for col in summary.columns]
        table.add_row(*row)
    console.print(table)


def print_top_values(df):
    top = insights.top_values(df)
    if not top:
        return
    console.print(Panel.fit("[bold cyan]Top Values (Categorical Columns)[/bold cyan]"))
    for col, values in top.items():
        table = Table(title=col, box=box.SIMPLE)
        table.add_column("Value", style="bold")
        table.add_column("Count")
        for val, count in values.items():
            table.add_row(str(val), str(count))
        console.print(table)


def print_outliers(df):
    outs = insights.outliers(df)
    if not outs:
        console.print("[green]No outliers detected.[/green]")
        return
    console.print(Panel.fit("[bold yellow]Outliers Detected[/bold yellow]"))
    for col, info in outs.items():
        console.print(f"  [yellow]{col}[/yellow]: {info['outlier_count']} outliers "
                      f"(outside [{info['lower_bound']}, {info['upper_bound']}])")


def auto_detect_columns(df):
    """Detect likely date, group, and value columns from the dataframe."""
    import pandas as pd

    date_col = next((c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])), None)
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    value_col = None
    for candidate in ["revenue", "profit", "sales", "amount", "total", "value"]:
        match = next((c for c in num_cols if candidate in c.lower()), None)
        if match:
            value_col = match
            break
    if not value_col and num_cols:
        value_col = num_cols[-1]

    group_col = None
    for candidate in ["region", "category", "product", "department", "segment"]:
        match = next((c for c in cat_cols if candidate in c.lower()), None)
        if match:
            group_col = match
            break
    if not group_col and cat_cols:
        group_col = cat_cols[0]

    return date_col, group_col, value_col


def main():
    parser = argparse.ArgumentParser(description="Analyze a CSV file for insights and charts.")
    parser.add_argument("csv_file", help="Path to the CSV file")
    parser.add_argument("--output", default="reports", help="Output directory for charts (default: reports)")
    parser.add_argument("--no-charts", action="store_true", help="Skip generating charts")
    args = parser.parse_args()

    console.print(f"\n[bold]Loading:[/bold] {args.csv_file}\n")

    try:
        df = load_csv(args.csv_file)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    # Overview
    info = insights.overview(df)
    print_overview(info)

    # Numeric summary
    print_numeric_summary(df)

    # Top categories
    print_top_values(df)

    # Outliers
    console.print(Panel.fit("[bold cyan]Outlier Analysis[/bold cyan]"))
    print_outliers(df)

    # Auto-detect key columns
    date_col, group_col, value_col = auto_detect_columns(df)

    # Group summary
    if group_col and value_col:
        console.print(Panel.fit(f"[bold cyan]{value_col} by {group_col}[/bold cyan]"))
        summary = insights.group_summary(df, group_col, value_col)
        table = Table(box=box.SIMPLE)
        table.add_column(group_col, style="bold")
        for col in summary.columns:
            table.add_column(col.title())
        for idx, row in summary.iterrows():
            table.add_row(str(idx), *[str(v) for v in row])
        console.print(table)

    # Monthly trend
    if date_col and value_col:
        console.print(Panel.fit(f"[bold cyan]Monthly Trend: {value_col}[/bold cyan]"))
        trend = insights.monthly_trend(df, date_col, value_col)
        table = Table(box=box.SIMPLE)
        table.add_column("Month", style="bold")
        table.add_column(value_col.title())
        for _, row in trend.iterrows():
            table.add_row(str(row["month"]), str(row[value_col]))
        console.print(table)

    # Charts
    if not args.no_charts:
        output_dir = Path(args.output)
        console.print(f"\n[bold]Generating charts → {output_dir}/[/bold]")
        saved = []
        saved += visualizer.plot_distributions(df, output_dir)
        saved += visualizer.plot_correlation_heatmap(df, output_dir)
        saved += visualizer.plot_top_categories(df, output_dir)
        if date_col and value_col:
            saved += visualizer.plot_monthly_trend(df, date_col, value_col, output_dir)
        if group_col and value_col:
            saved += visualizer.plot_group_comparison(df, group_col, value_col, output_dir)
        for path in saved:
            console.print(f"  [green]✓[/green] {path}")

    console.print("\n[bold green]Analysis complete.[/bold green]\n")


if __name__ == "__main__":
    main()
