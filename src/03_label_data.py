# 03_label_data.py - Create "minutes until failure" labels
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

print("="*70)
print("DATA LABELING - Creating Time to Failure")
print("="*70)

# Find your aggressive data file
data_files = glob.glob('data\\raw\\network_data_aggressive_*.csv')
if not data_files:
    data_files = glob.glob('data\\raw\\network_data_*.csv')

if not data_files:
    print("[ERROR] No data files found!")
    exit()

latest_file = max(data_files, key=os.path.getctime)
print(f"\n[LOADING] {latest_file}\n")

df = pd.read_csv(latest_file)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"[DATA] Loaded {len(df)} measurements")
print(f"[ROUNDS] {df['round_id'].max()} rounds")
print(f"[FAILURES] {len(df[df['packet_loss_percent'] > 0])} measurements with loss")

# Create a new dataframe for labeling
labeled_data = []

# Group by round to process each round's data
for round_num in range(1, df['round_id'].max() + 1):
    round_data = df[df['round_id'] == round_num]
    
    if len(round_data) < 2:
        continue
    
    # Get router and DNS data for this round
    router_row = round_data[round_data['target'] == 'router'].iloc[0]
    dns_row = round_data[round_data['target'] == 'dns'].iloc[0]
    
    # Calculate time to failure
    # Look ahead up to 20 rounds (about 2-3 minutes with 2 sec waits)
    future_rounds = df[df['round_id'] > round_num]
    
    # Check if there's a failure in next 20 rounds
    future_failures = future_rounds[
        (future_rounds['round_id'] <= round_num + 20) & 
        (future_rounds['packet_loss_percent'] > 50)
    ]
    
    if len(future_failures) > 0:
        # Get the earliest failure
        first_failure = future_failures.iloc[0]
        rounds_until_failure = first_failure['round_id'] - round_num
        # Convert rounds to minutes (each round takes ~2-3 seconds)
        minutes_to_failure = rounds_until_failure * 0.05  # ~3 seconds per round
        minutes_to_failure = min(minutes_to_failure, 10)  # Cap at 10 minutes
    else:
        minutes_to_failure = 10  # Healthy, no failure in next 10 min
    
    # Create features
    features = {
        'round_id': round_num,
        'timestamp': router_row['timestamp'],
        'router_latency_ms': router_row['latency_ms'],
        'router_packet_loss_pct': router_row['packet_loss_percent'],
        'dns_latency_ms': dns_row['latency_ms'],
        'dns_packet_loss_pct': dns_row['packet_loss_percent'],
        'rssi_dbm': router_row['rssi_dbm'],
        'minutes_to_failure': minutes_to_failure,
        'is_critical': 1 if minutes_to_failure < 2 else 0  # Binary: failing soon?
    }
    
    labeled_data.append(features)

# Create labeled dataframe
df_labeled = pd.DataFrame(labeled_data)

# Add derived features (trends)
df_labeled['router_latency_trend'] = df_labeled['router_latency_ms'].diff().fillna(0)
df_labeled['dns_latency_trend'] = df_labeled['dns_latency_ms'].diff().fillna(0)
df_labeled['avg_latency'] = (df_labeled['router_latency_ms'] + df_labeled['dns_latency_ms']) / 2

# Rolling averages (last 5 rounds)
for col in ['router_latency_ms', 'dns_latency_ms', 'router_packet_loss_pct', 'dns_packet_loss_pct']:
    df_labeled[f'{col}_rolling5'] = df_labeled[col].rolling(5, min_periods=1).mean()

print("\n" + "="*70)
print("LABELED DATA SUMMARY")
print("="*70)
print(f"Total labeled rounds: {len(df_labeled)}")
print(f"Critical failures (<2 min): {len(df_labeled[df_labeled['is_critical'] == 1])}")
print(f"Healthy (>5 min to fail): {len(df_labeled[df_labeled['minutes_to_failure'] > 5])}")

print("\nMinutes to failure distribution:")
for mins in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    count = len(df_labeled[df_labeled['minutes_to_failure'] == mins])
    if count > 0:
        bar = "=" * (count // 2)
        print(f"  {mins:2d} minutes: {bar} ({count} rounds)")

# Save labeled data
output_folder = "data\\processed"
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, f'labeled_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
df_labeled.to_csv(output_file, index=False)

print(f"\n[SAVED] {output_file}")

# Show sample
print("\n" + "="*70)
print("SAMPLE LABELED DATA (first 10 rows)")
print("="*70)
print(df_labeled[['round_id', 'router_packet_loss_pct', 'dns_packet_loss_pct', 
                  'minutes_to_failure', 'is_critical']].head(10).to_string())

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("[OK] Data labeling complete!")
print("-> Run 04_train_model.py to train your first AI model")

# Create a simple visualization
try:
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.hist(df_labeled['minutes_to_failure'], bins=20, edgecolor='black')
    plt.xlabel('Minutes to Failure')
    plt.ylabel('Number of Rounds')
    plt.title('Distribution: Time to Failure')
    plt.axvline(x=2, color='red', linestyle='--', label='Critical (<2 min)')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    plt.scatter(df_labeled['router_packet_loss_pct'], df_labeled['minutes_to_failure'], alpha=0.5)
    plt.xlabel('Router Packet Loss (%)')
    plt.ylabel('Minutes to Failure')
    plt.title('Packet Loss vs Time to Failure')
    plt.gca().invert_yaxis()  # Less time = closer to failure
    
    plt.tight_layout()
    plt.savefig('data/label_distribution.png')
    print("\n[CHART] Saved to data/label_distribution.png")
except:
    print("\n[NOTE] Install matplotlib for charts: python -m pip install matplotlib")

print("="*70)