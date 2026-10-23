# ALLADIN Machine Learning Model Registry

**Last Updated:** 2026-10-21 12:45:42  
**Evaluation Strategy:** Strict Cross-Business Generalization (Dev Companies 1 & 2 vs Strictly Held-Out Company 3).

| Pipeline | Selected Algorithm | Primary Canonical Artifact | Dev Val Metric | Dev Test Metric | Holdout Co3 Performance | Status |
|---|---|---|---|---|---|---|
| **revenue_forecasting** | AAGF_Custom | `revenue_forecasting_selected.pkl` | Verified | Verified | WAPE: 15.18% | production |
| **sales_forecasting** | AAGF_Custom | `sales_forecasting_selected.pkl` | WAPE: 58.47% | WAPE: 54.06% | WAPE: 52.97% | production |
| **inventory_prediction** | LightGBM | `inventory_demand_selected.pkl` | WAPE: 58.37% | WAPE: 55.59% | WAPE: 54.59% | production |
| **profit_prediction** | LightGBM | `profit_prediction_selected.pkl` | WAPE: 7.31% | WAPE: 8.57% | WAPE: 8.98% | production |
| **expense_prediction** | LightGBM | `expense_prediction_selected.pkl` | WAPE: 16.99% | WAPE: 16.45% | WAPE: 18.90% | production |
| **business_health_score** | TransparentKPIScorecard + Random_Forest | `health_score_pipeline.pkl` | Verified | Verified | WAPE: 8.69% | production |
| **anomaly_detection** | Isolation_Forest | `anomaly_detection_isolation_forest.pkl` | F1: 0.6250 | F1: 0.4444 | F1: 0.3692 | production |
