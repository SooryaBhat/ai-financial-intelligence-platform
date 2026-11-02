import sys
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
train_df = dev_df[train_mask].copy()
y_train = train_df["quantity"].values

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

# Test forward prediction on aggregate history
curr_history = [456.0, 376.0, 467.0, 527.0, 483.0, 415.0, 620.0, 742.0, 515.0, 584.0]
while len(curr_history) < 12:
    curr_history.insert(0, curr_history[0])

start_year, start_month = 2026, 10
preds = []
for i in range(6):
    m_idx = (start_month + i - 1) % 12 + 1
    y_idx = start_year + (start_month + i - 1) // 12
    quarter = (m_idx - 1) // 3 + 1
    feat_dict = {
        'lag_1': curr_history[-1],
        'lag_2': curr_history[-2],
        'lag_3': curr_history[-3],
        'lag_12': curr_history[-12],
        'roll3_mean': float(np.mean(curr_history[-3:])),
        'roll6_mean': float(np.mean(curr_history[-6:])),
        'roll3_std': float(np.std(curr_history[-3:])),
        'month_num': float(m_idx),
        'quarter': float(quarter),
        'year': float(y_idx),
        'is_q4': 1.0 if quarter == 4 else 0.0,
        'is_q1': 1.0 if quarter == 1 else 0.0,
    }
    feat_df = pd.DataFrame([feat_dict])
    pred_units = float(ppf_fixed.predict(feat_df)[0])
    preds.append((f"{y_idx}-{m_idx:02d}", round(pred_units, 2)))
    curr_history.append(pred_units)

print("Aggregate input forecast with Fixed PPF:", preds)
