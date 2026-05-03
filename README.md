# CSV Data Analyzer

A command-line tool to load any CSV file and instantly get data insights, statistics, and charts.

## Features

- Dataset overview (rows, columns, missing values, duplicates)
- Numeric statistics (mean, median, std, min, max, percentiles)
- Top value counts for categorical columns
- Outlier detection using IQR method
- Group summaries (total, average, transaction count)
- Monthly trend analysis (auto-detects date columns)
- Auto-generated charts:
  - Distribution plots
  - Correlation heatmap
  - Top category bar charts
  - Monthly trend line
  - Group comparison bar chart

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Analyze the included sample data
python main.py data/sample_sales.csv

# Analyze your own CSV
python main.py path/to/your/file.csv

# Skip chart generation
python main.py data/sample_sales.csv --no-charts

# Save charts to a custom folder
python main.py data/sample_sales.csv --output my_reports
```

## Output

- Terminal: formatted tables with all insights
- `reports/` folder: PNG charts saved automatically

## Sample Data

Includes `data/sample_sales.csv` — a sales dataset with region, product, revenue, and profit columns for testing.
