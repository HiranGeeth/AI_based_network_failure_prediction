# 04_train_model.py - Train XGBoost model to predict failures
import pandas as pd
import numpy as np
import os
import glob
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
import xgboost as xgb
import joblib

print("="*70)
print("AI MODEL TRAINING - Predictive Maintenance")
print("="*70)

# Find labeled data
labeled_files = glob.glob('data\\processed\\labeled_data_*.csv')
if not labeled_files:
    print("[ERROR] No labeled data found!")
    print("Run 03_label_data.py first")
    exit()

latest_file = max(labeled_files, key=os.path.getctime)
print(f"\n[LOADING] {latest_file}\n")

df = pd.read_csv(latest_file)
print(f"[DATA] Loaded {len(df)} labeled rounds")

# Features for training (what the AI learns from)
feature_columns = [
    'router_latency_ms',
    'router_packet_loss_pct', 
    'dns_latency_ms',
    'dns_packet_loss_pct',
    'router_latency_ms_rolling5',
    'dns_latency_ms_rolling5',
    'router_packet_loss_pct_rolling5',
    'dns_packet_loss_pct_rolling5',
    'router_latency_trend',
    'dns_latency_trend',
    'avg_latency'
]

# Target (what the AI predicts)
target_column = 'minutes_to_failure'

# Remove rows with NaN
df_clean = df[feature_columns + [target_column]].dropna()
print(f"[CLEAN] {len(df_clean)} usable rows after removing NaN")

X = df_clean[feature_columns]
y = df_clean[target_column]

print(f"\n[FEATURES] {len(feature_columns)} input features:")
for i, f in enumerate(feature_columns, 1):
    print(f"  {i:2d}. {f}")

print(f"\n[TARGET] {target_column} (0-10 minutes)")

# Split into training and testing
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"\n[TRAIN] {len(X_train)} samples")
print(f"[TEST] {len(X_test)} samples")

# Train XGBoost model
print("\n[LEARNING] Training XGBoost model...")

model = xgb.XGBRegressor(
    n_estimators=100,  # Number of trees
    max_depth=4,       # Tree depth (simpler is better for small data)
    learning_rate=0.1,
    objective='reg:squarederror',
    random_state=42
)

model.fit(X_train, y_train)

# Predict on test data
y_pred = model.predict(X_test)

# Calculate accuracy
mae = mean_absolute_error(y_test, y_pred)
print(f"\n[RESULT] Mean Absolute Error: {mae:.2f} minutes")
print(f"[RESULT] Model predicts failure within {mae:.1f} minutes of actual time")

# Calculate classification accuracy (critical vs not critical)
y_test_critical = (y_test < 2).astype(int)
y_pred_critical = (y_pred < 2).astype(int)
class_accuracy = accuracy_score(y_test_critical, y_pred_critical)
print(f"[RESULT] Critical failure detection accuracy: {class_accuracy*100:.1f}%")

# Feature importance
print("\n[IMPORTANCE] What the AI learned matters most:")
importance = model.feature_importances_
feature_importance = sorted(zip(feature_columns, importance), key=lambda x: x[1], reverse=True)

for feature, imp in feature_importance[:5]:
    bar = "=" * int(imp * 50)
    print(f"  {bar} {imp*100:.1f}% - {feature}")

# Save model
model_folder = "models"
os.makedirs(model_folder, exist_ok=True)
model_file = os.path.join(model_folder, 'failure_predictor.pkl')
joblib.dump(model, model_file)

# Save feature columns for later use
feature_file = os.path.join(model_folder, 'feature_columns.pkl')
joblib.dump(feature_columns, feature_file)

print(f"\n[SAVED] Model to {model_file}")
print(f"[SAVED] Features to {feature_file}")

# Create a simple test prediction
print("\n" + "="*70)
print("TEST PREDICTION - Example")
print("="*70)

# Example: Current network state
example_input = pd.DataFrame([[
    50,    # router_latency_ms
    20,    # router_packet_loss_pct
    150,   # dns_latency_ms  
    10,    # dns_packet_loss_pct
    50,    # router_latency_ms_rolling5
    150,   # dns_latency_ms_rolling5
    20,    # router_packet_loss_pct_rolling5
    10,    # dns_packet_loss_pct_rolling5
    5,     # router_latency_trend
    10,    # dns_latency_trend
    100    # avg_latency
]], columns=feature_columns)

prediction = model.predict(example_input)[0]
print(f"Current state: Router loss=20%, DNS loss=10%, Latency=50ms")
print(f"Predicted time to failure: {prediction:.1f} minutes")
print(f"Status: {'CRITICAL' if prediction < 2 else 'WARNING' if prediction < 5 else 'HEALTHY'}")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("[OK] Model training complete!")
print("-> Run 05_predict_live.py to test on new data")
print("="*70)