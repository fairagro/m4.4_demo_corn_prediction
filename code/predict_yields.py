import pandas as pd
import joblib
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-f", "--features", dest="features", default="county_features_cache.csv")
parser.add_option("-m", "--model", dest="model_file", default="rf_model.pkl")
parser.add_option("-s", "--scaler", dest="scaler_file", default="scaler.pkl")
(options, args) = parser.parse_args()

# Load features and model
features_df = pd.read_csv(options.features)
model = joblib.load(options.model_file)
scaler = joblib.load(options.scaler_file)

# Select the same feature columns used for training
feature_cols = ["temp_mean","temp_std","rain_sum","rain_std","clay","silt","sand","soc","ph"]
X_df = features_df[feature_cols]

# Impute missing values (in case there are NaNs)
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy="mean")
X_imputed = imputer.fit_transform(X_df)  # optionally: fit on train imputer separately

# Keep as DataFrame to preserve column names for scaler
X_scaled = scaler.transform(pd.DataFrame(X_imputed, columns=feature_cols))

# Predict
features_df["Predicted_Yield"] = model.predict(X_scaled)

# Save predictions
features_df.to_csv("county_predictions.csv", index=False)
