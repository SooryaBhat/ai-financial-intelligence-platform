import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

sys.path.insert(0, 'ml/scripts')
sys.path.insert(0, 'ml/scripts/custom_models')
from utils import PROCESSED_DIR, load_csv, compute_metrics, SPLIT_CONFIG, DEV_COMPANIES, HOLDOUT_COMPANY
from custom_models.product_profile_model import ProductProfileForecaster

df = load_csv("sales_features.csv", PROCESSED_DIR)
df["month"] = pd.to_datetime(df["month"])
df = df.sort_values(["company_id", "product_id", "month"]).reset_index(drop=True)

dev_df = df[df["company_id"].isin(DEV_COMPANIES)].copy()
train_mask = (dev_df["month"] <= SPLIT_CONFIG["train_end"])
val_mask = (dev_df["month"] >= SPLIT_CONFIG["val_start"]) & (dev_df["month"] <= SPLIT_CONFIG["val_end"])
test_mask = (dev_df["month"] >= SPLIT_CONFIG["test_start"])

train_df = dev_df[train_mask].copy()
val_df = dev_df[val_mask].copy()
test_df = dev_df[test_mask].copy()
holdout_df = df[df["company_id"] == HOLDOUT_COMPANY].copy()

y_train = train_df["quantity"].values
y_val = val_df["quantity"].values
y_test = test_df["quantity"].values

print("--- CURRENT PPF (with leakage) ---")
ppf_leak = ProductProfileForecaster(alpha=1.0, random_state=42)
ppf_leak.fit(train_df, y_train)
val_pred_leak = np.maximum(0, ppf_leak.predict(val_df))
m_leak = compute_metrics(y_val, val_pred_leak, y_train)
print("Val WAPE (leak):", m_leak["wape"])
print("Feature cols:", ppf_leak.feature_cols_)
print("Coefs:", dict(zip(ppf_leak.feature_cols_, ppf_leak.ridge_model_.coef_)))

print("\n--- FIXED PPF (without quantity in features) ---")
class FixedPPF(ProductProfileForecaster):
    def fit(self, X: pd.DataFrame, y: np.ndarray):
        y_arr = np.asarray(y, dtype=np.float64).ravel()
        n = len(y_arr)
        if isinstance(X, pd.DataFrame):
            self.feature_cols_ = [col for col in X.columns if col not in ["product_id", "company_id", "month", "quantity", "target", "y"]]
            if "product_id" in X.columns:
                product_means = pd.Series(y_arr).groupby(X["product_id"].values).mean()
                self.product_velocity_ = product_means.to_dict()
                self.global_mean_velocity_ = float(np.mean(y_arr)) if n > 0 else 10.0
            X_num = X[self.feature_cols_].select_dtypes(include=[np.number]).fillna(0.0).values
        else:
            X_num = np.asarray(X, dtype=np.float64)

        if isinstance(X, pd.DataFrame) and "product_id" in X.columns:
            base_vel = np.array([self.product_velocity_.get(pid, self.global_mean_velocity_) for pid in X["product_id"].values])
        else:
            base_vel = np.full(n, self.global_mean_velocity_)

        residuals = y_arr - base_vel
        self.ridge_model_ = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.ridge_model_.fit(X_num, residuals)
        self.is_fitted_ = True
        return self

ppf_fixed = FixedPPF(alpha=1.0, random_state=42)
ppf_fixed.fit(train_df, y_train)
val_pred_fixed = np.maximum(0, ppf_fixed.predict(val_df))
m_fixed = compute_metrics(y_val, val_pred_fixed, y_train)
print("Val WAPE (fixed):", m_fixed["wape"])
print("Feature cols:", ppf_fixed.feature_cols_)
print("Coefs:", dict(zip(ppf_fixed.feature_cols_, ppf_fixed.ridge_model_.coef_)))
