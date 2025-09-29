#!/usr/bin/env python3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.impute import SimpleImputer
import joblib
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--features", dest="features", default="county_features.csv")
parser.add_option("-y", "--yield", dest="yield_csv", default="iowa_yield.csv")
parser.add_option("--interactions", dest="interactions", action="store_true", default=False,
                  help="Add interaction features between soil and weather")
(options, args) = parser.parse_args()

# -------------------------------
# Load data
# -------------------------------
features_df = pd.read_csv(options.features)
yield_df = pd.read_csv(options.yield_csv)

# Filter yield data for corn grain
yield_df = yield_df[yield_df["short_desc"].str.contains("CORN, GRAIN", na=False)]
yield_df = yield_df[["county_name", "Value"]].rename(columns={"Value": "Yield"})
yield_df["Yield"] = (
    yield_df["Yield"].astype(str).str.replace(",", "", regex=False)
).astype(float)
yield_df["county_name_norm"] = yield_df["county_name"].str.upper()

# Merge
df = features_df.merge(yield_df, on="county_name_norm", how="inner").dropna(subset=["Yield"])

# -------------------------------
# Features
# -------------------------------
weather_cols = ["temp_mean","temp_std","rain_sum","rain_std"]
soil_cols = ["clay","silt","sand","soc","ph"]

X_base = df[weather_cols + soil_cols].copy()
y = df["Yield"].values

# Impute missing values with column mean
imputer = SimpleImputer(strategy="mean")
X_imputed = imputer.fit_transform(X_base)

# Optional: add interaction features
if options.interactions:
    poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
    X_interactions = poly.fit_transform(X_imputed)
    interaction_feature_names = poly.get_feature_names_out(weather_cols + soil_cols)
    X = pd.DataFrame(X_interactions, columns=interaction_feature_names)
else:
    X = pd.DataFrame(X_imputed, columns=weather_cols + soil_cols)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# -------------------------------
# Train/Test split
# -------------------------------
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# -------------------------------
# Train RandomForest
# -------------------------------
model = RandomForestRegressor(
    n_estimators=500,
    max_depth=20,
    min_samples_leaf=3,
    max_features="sqrt",
    n_jobs=-1,
    random_state=42
)
model.fit(X_train, y_train)

# -------------------------------
# Evaluate
# -------------------------------
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
print(f"Test R^2: {r2:.4f}")
mae = mean_absolute_error(y_test, y_pred)
print(f"Test MAE: {mae:.2f}")
cv_scores = cross_val_score(model, X_scaled, y, cv=10, scoring="r2")

# -------------------------------
# Save model and scaler
# -------------------------------
joblib.dump(model, "model.pkl")
joblib.dump(scaler, "scaler.pkl")