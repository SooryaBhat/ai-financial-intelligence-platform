# ALLADIN Machine Learning Model Registry

**Last Updated:** 2026-11-02 21:37:53  
**Evaluation Strategy:** Strict Cross-Business Generalization (Dev Companies 1 & 2 vs Strictly Held-Out Company 3).

| Pipeline | Selected Algorithm | Primary Canonical Artifact | Dev Val Metric | Dev Test Metric | Holdout Co3 Performance | Status |
|---|---|---|---|---|---|---|
| **revenue_forecasting** | AAGF_Custom | `revenue_forecasting_selected.pkl` | WAPE: 13.78% | WAPE: 16.91% | WAPE: 11.87% | production |
| **sales_forecasting** | CatBoost | `sales_forecasting_selected.pkl` | WAPE: 56.26% | WAPE: 58.11% | WAPE: 53.39% | production |
| **inventory_prediction** | LightGBM | `inventory_demand_selected.pkl` | WAPE: 56.88% | WAPE: 58.19% | WAPE: 53.70% | production |
| **profit_prediction** | LightGBM | `profit_prediction_selected.pkl` | WAPE: 12.15% | WAPE: 18.73% | WAPE: 11.08% | production |
| **expense_prediction** | Random_Forest | `expense_prediction_selected.pkl` | WAPE: 19.10% | WAPE: 19.58% | WAPE: 18.00% | production |
| **business_health_score** | TransparentKPIScorecard + Linear_Regression | `health_score_selected.pkl` | MAE: 4.75 pts | MAE: 3.76 pts | MAE: 2.92 pts | production |
| **anomaly_detection** | Rule_Based_Detector | `anomaly_detection_selected.pkl` | F1: 0.6667 | F1: 0.8947 | F1: 0.6379 | production |
