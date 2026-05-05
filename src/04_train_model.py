# 04_train_model.py - Train XGBoost model on labeled data
import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb
from datetime import datetime

print("="*70)
print("TRAINING PREDICTIVE MAINTENANCE MODEL")
print("="*70)

# Find the most recent Excel file
data_folder = "data"
excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]

if not excel_files:
    print("[ERROR] No Excel files found in data folder!")
    print("Run create_excel_data.py first")
    exit()

latest_file = max(excel_files, key=lambda x: os.path.getctime(os.path.join(data_folder, x)))
file_path = os.path.join(data_folder, latest_file)

print(f"\n[LOADING] {latest_file}")
df = pd.read_excel(file_path, engine='openpyxl')
print(f"[ROWS] {len(df)} rounds")
print(f"[COLUMNS] {len(df.columns)} features")

# Define features (X) and target (y)
feature_columns = [
    'router_ping_ms',
    'dns_ping_ms', 
    'rssi_dbm',
    'router_ping_rolling5',
    'dns_ping_rolling5',
    'rssi_rolling5',
    'router_trend',
    'dns_trend',
    'rssi_trend'
]

target_column = 'minutes_to_failure'

# Prepare data
X = df[feature_columns].copy()
y = df[target_column].copy()

# Remove any rows with NaN (if any)
X = X.fillna(0)
y = y.fillna(10)

print(f"\n[FEATURES] {len(feature_columns)} inputs")
for i, f in enumerate(feature_columns, 1):
    print(f"  {i:2d}. {f}")

print(f"\n[TARGET] {target_column} (0-10 minutes)")

# Split into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n[TRAIN SET] {len(X_train)} samples")
print(f"[TEST SET] {len(X_test)} samples")

# Train XGBoost model
print("\n[LEARNING] Training XGBoost Regressor...")

model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    objective='reg:squarederror',
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("\n" + "="*70)
print("MODEL PERFORMANCE")
print("="*70)
print(f"Mean Absolute Error (MAE): {mae:.2f} minutes")
print(f"R² Score: {r2:.3f}")
print(f"Accuracy: Within {(mae/10)*100:.1f}% of actual time")

# Critical detection accuracy (failure within 2 minutes)
y_test_critical = (y_test < 2).astype(int)
y_pred_critical = (y_pred < 2).astype(int)
critical_accuracy = (y_test_critical == y_pred_critical).mean() * 100
print(f"Critical Failure Detection (<2 min): {critical_accuracy:.1f}%")

# Feature importance
print("\n" + "="*70)
print("FEATURE IMPORTANCE (What AI Learned)")
print("="*70)
importance = model.feature_importances_
feature_importance = sorted(zip(feature_columns, importance), key=lambda x: x[1], reverse=True)

for feature, imp in feature_importance:
    bar_length = int(imp * 50)
    bar = "=" * bar_length
    print(f"  {bar:50} {imp*100:.1f}% - {feature}")

# Save model
model_folder = "models"
os.makedirs(model_folder, exist_ok=True)
model_file = os.path.join(model_folder, f'failure_predictor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl')
joblib.dump(model, model_file)

# Save feature columns
feature_file = os.path.join(model_folder, 'feature_columns.pkl')
joblib.dump(feature_columns, feature_file)

print("\n" + "="*70)
print("MODEL SAVED")
print("="*70)
print(f"[MODEL] {model_file}")
print(f"[FEATURES] {feature_file}")

# Test prediction example
print("\n" + "="*70)
print("TEST PREDICTION EXAMPLES")
print("="*70)

# Example 1: Healthy network (based on early rounds in your data)
healthy = [[
    5,      # router_ping_ms
    45,     # dns_ping_ms
    -55,    # rssi_dbm
    6,      # router_ping_rolling5
    50,     # dns_ping_rolling5
    -56,    # rssi_rolling5
    0,      # router_trend
    1,      # dns_trend
    -1      # rssi_trend
]]
pred_healthy = model.predict(healthy)[0]
print(f"\n[HEALTHY NETWORK] Router=5ms, DNS=45ms, RSSI=-55dBm")
print(f"  -> Predicted: {pred_healthy:.1f} minutes to failure")
if pred_healthy > 8:
    print("  -> Status: GOOD - No action needed")
elif pred_healthy > 5:
    print("  -> Status: DEGRADING - Monitor")
elif pred_healthy > 2:
    print("  -> Status: WARNING - Prepare")
else:
    print("  -> Status: CRITICAL - Take action")

# Example 2: Degrading network (based on round 42-46 in your data)
degrading = [[
    30,     # router_ping_ms
    200,    # dns_ping_ms
    -80,    # rssi_dbm
    25,     # router_ping_rolling5
    150,    # dns_ping_rolling5
    -75,    # rssi_rolling5
    15,     # router_trend
    80,     # dns_trend
    -10     # rssi_trend
]]
pred_degrading = model.predict(degrading)[0]
print(f"\n[DEGRADING NETWORK] Router=30ms, DNS=200ms, RSSI=-80dBm")
print(f"  -> Predicted: {pred_degrading:.1f} minutes to failure")
if pred_degrading > 8:
    print("  -> Status: GOOD - No action needed")
elif pred_degrading > 5:
    print("  -> Status: DEGRADING - Monitor")
elif pred_degrading > 2:
    print("  -> Status: WARNING - Prepare")
else:
    print("  -> Status: CRITICAL - Take action")

# Example 3: Critical network (based on round 62 in your data - full outage)
critical = [[
    9999,   # router_ping_ms
    9999,   # dns_ping_ms
    -100,   # rssi_dbm
    2000,   # router_ping_rolling5
    2000,   # dns_ping_rolling5
    -100,   # rssi_rolling5
    0,      # router_trend
    0,      # dns_trend
    0       # rssi_trend
]]
pred_critical = model.predict(critical)[0]
print(f"\n[CRITICAL NETWORK] Router=9999ms (timeout), DNS=9999ms, RSSI=-100dBm")
print(f"  -> Predicted: {pred_critical:.1f} minutes to failure")
if pred_critical > 8:
    print("  -> Status: GOOD - No action needed")
elif pred_critical > 5:
    print("  -> Status: DEGRADING - Monitor")
elif pred_critical > 2:
    print("  -> Status: WARNING - Prepare")
else:
    print("  -> Status: CRITICAL - Take action")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. Run 05_predict_live.py for real-time monitoring")
print("2. Deploy to Raspberry Pi for 24/7 monitoring")
print("="*70)