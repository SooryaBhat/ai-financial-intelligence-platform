# ALLADIN Machine Learning Model Registry

**Last Updated:** 2026-11-02 22:37:17  
**Evaluation Strategy:** Strict Cross-Business Generalization (Dev Companies 1 & 2 vs Strictly Held-Out Company 3).

| Pipeline | Selected Algorithm | Primary Canonical Artifact | Dev Val Metric | Dev Test Metric | Holdout Co3 Performance | Status |
|---|---|---|---|---|---|---|
| **revenue_forecasting** | AAGF_Custom | `revenue_forecasting_selected.pkl` | WAPE: 15.15% | WAPE: 17.06% | WAPE: 10.94% | production |
| **sales_forecasting** | CatBoost | `sales_forecasting_selected.pkl` | WAPE: 56.18% | WAPE: 57.14% | WAPE: 53.40% | production |
| **inventory_prediction** | LightGBM | `inventory_demand_selected.pkl` | WAPE: 56.99% | WAPE: 57.94% | WAPE: 53.60% | production |
| **profit_prediction** | CatBoost | `profit_prediction_selected.pkl` | WAPE: 11.41% | WAPE: 19.22% | WAPE: 10.64% | production |
| **expense_prediction** | Random_Forest | `expense_prediction_selected.pkl` | WAPE: 19.10% | WAPE: 19.58% | WAPE: 18.00% | production |
| **business_health_score** | TransparentKPIScorecard + Linear_Regression | `health_score_selected.pkl` | MAE: 4.75 pts | MAE: 3.76 pts | MAE: 2.92 pts | production |
| **anomaly_detection** | Supervised_CatBoost | `anomaly_detection_selected.pkl` | F1: 0.9231 | F1: 0.8780 | F1: 0.7552 | production |
