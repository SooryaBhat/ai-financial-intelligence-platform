# ML Module — AI Financial Intelligence Platform

This directory contains all machine learning development assets for the AI Financial Intelligence Platform.

## Purpose

The ML module is responsible for:

- **Revenue Forecasting** — Predict future revenue based on historical trends
- **Sales Forecasting** — Predict product and category-level sales
- **Inventory Prediction** — Anticipate stock needs and prevent stockouts
- **Profit Prediction** — Forecast profit margins and net profit
- **Expense Prediction** — Detect anomalous or foreseeable expense changes
- **Business Health Scoring** — Composite AI score per company/branch
- **Anomaly Detection** — Detect fraud, data entry errors, unusual patterns

---

## Directory Structure

```
ml/
│
├── datasets/           # All datasets (raw, processed, synthetic)
│   ├── raw/            # Unmodified source data
│   ├── processed/      # Cleaned and feature-engineered data
│   ├── synthetic/      # Synthetic ERP data for development
│   └── README.md       # Dataset documentation
│
├── notebooks/          # Jupyter notebooks for exploration and experiments
│
├── scripts/            # Reusable Python scripts for training and prediction
│
├── models/             # Saved model artifacts (.pkl, .joblib, .onnx, etc.)
│
├── reports/            # Model evaluation reports and plots
│
├── configs/            # YAML configuration files for experiments
│
└── README.md           # This file
```

---

## Notebooks Overview

| Notebook | Purpose |
|----------|---------|
| `01_data_exploration.ipynb` | Exploratory Data Analysis (EDA) of all datasets |
| `02_data_preprocessing.ipynb` | Cleaning, encoding, and transformation pipeline |
| `03_revenue_forecasting.ipynb` | Revenue prediction using time-series models |
| `04_sales_forecasting.ipynb` | SKU/category-level sales forecasting |
| `05_inventory_prediction.ipynb` | Inventory demand prediction |
| `06_profit_prediction.ipynb` | Profit margin and net profit forecasting |
| `07_expense_prediction.ipynb` | Expense trend modeling |
| `08_business_health_score.ipynb` | Composite business health scoring |
| `09_anomaly_detection.ipynb` | Anomaly and fraud detection |
| `10_model_comparison.ipynb` | Cross-model benchmarking and selection |

---

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `preprocess.py` | Data cleaning and preprocessing pipeline |
| `feature_engineering.py` | Feature creation and selection |
| `train_revenue.py` | Train revenue forecasting models |
| `train_sales.py` | Train sales forecasting models |
| `train_inventory.py` | Train inventory demand models |
| `train_profit.py` | Train profit prediction models |
| `train_expenses.py` | Train expense prediction models |
| `train_health_score.py` | Train business health scoring model |
| `train_anomaly.py` | Train anomaly detection models |
| `evaluate.py` | Evaluate model performance (RMSE, MAE, MAPE, etc.) |
| `predict.py` | Run inference with trained models |
| `utils.py` | Shared utility functions |

---

## Getting Started

### 1. Set up Python environment

```bash
cd ml/
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 2. Explore synthetic data

The `datasets/synthetic/` folder contains realistic ERP data for development.
See `datasets/README.md` for full documentation.

### 3. Run notebooks

```bash
jupyter lab
```

Open any notebook in the `notebooks/` folder.

---

## Tech Stack (Planned)

- **Python 3.11+**
- **Pandas / NumPy** — Data manipulation
- **Scikit-learn** — Classical ML models
- **XGBoost / LightGBM** — Gradient boosting
- **Prophet / statsmodels** — Time-series forecasting
- **SHAP** — Model interpretability
- **Matplotlib / Seaborn / Plotly** — Visualization
- **MLflow** — Experiment tracking (planned)
- **FastAPI** — Model serving (via backend integration)

---

## Notes

- Do **not** commit large model files or raw data to Git.
- Use `.gitignore` to exclude `models/`, `datasets/raw/`, and `datasets/processed/`.
- All model endpoints will eventually be served via the FastAPI backend.
- Follow the project's coding standards and documentation practices.
