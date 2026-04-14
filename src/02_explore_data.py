# 02_explore_data.py - Analyze your collected data
import pandas as pd
import os
import glob

print("="*60)
print("DATA EXPLORATION TOOL")
print("="*60)

# Find your data file
data_files = glob.glob('data\\raw\\network_data_*.csv')

if not data_files:
    print("[ERROR] No data files found in data\\raw\\")
    print("Please run 01_data_collection_auto.py first")
    exit()

# Load the most recent file
latest_file = max(data_files, key=os.path.getctime)
print(f"\n[LOADING] {latest_file}\n")

df = pd.read_csv(latest_file)

# Basic info
print("="*60)
print("FILE SUMMARY")
print("="*60)
print(f"Total measurements: {len(df)}")
print(f"Router measurements: {len(df[df['target']=='router'])}")
print(f"DNS measurements: {len(df[df['target']=='dns'])}")
print(f"Rounds completed: {df['round_id'].max()}")

print("\n" + "="*60)
print("DATA QUALITY CHECK")
print("="*60)

# Check RSSI (stuck at -60?)
unique_rssi = df['rssi_dbm'].unique()
print(f"Unique RSSI values: {sorted(unique_rssi)[:10]}")
if len(unique_rssi) == 1 and unique_rssi[0] == -60:
    print("[WARNING] RSSI is stuck at -60 - Windows not reporting signal strength")
    print("         This is OK - we'll train without RSSI")
else:
    print("[OK] RSSI varies - good for training")

# Check packet loss
print(f"\nPacket loss range: {df['packet_loss_percent'].min()}% to {df['packet_loss_percent'].max()}%")
loss_distribution = df['packet_loss_percent'].value_counts().sort_index()
print("\nPacket loss distribution:")
for loss, count in loss_distribution.head(10).items():
    bar = "=" * (count // 2)
    print(f"  {loss:3d}% loss: {bar} ({count} measurements)")

# Check failures
failures = df[df['packet_loss_percent'] > 0]
print(f"\nMeasurements with packet loss (>0%): {len(failures)}")
print(f"Measurements with high loss (>20%): {len(df[df['packet_loss_percent'] > 20])}")
print(f"Complete failures (100% loss): {len(df[df['packet_loss_percent'] == 100])}")

# Latency statistics
print("\n" + "="*60)
print("LATENCY STATISTICS")
print("="*60)
print("\nRouter latency:")
router_df = df[df['target']=='router']
print(f"  Min: {router_df['latency_ms'].min():.0f}ms")
print(f"  Max: {router_df['latency_ms'].max():.0f}ms")
print(f"  Avg: {router_df['latency_ms'].mean():.0f}ms")

print("\nDNS latency:")
dns_df = df[df['target']=='dns']
print(f"  Min: {dns_df['latency_ms'].min():.0f}ms")
print(f"  Max: {dns_df['latency_ms'].max():.0f}ms")
print(f"  Avg: {dns_df['latency_ms'].mean():.0f}ms")

# Show when failures happened
print("\n" + "="*60)
print("FAILURE TIMELINE")
print("="*60)
failure_rounds = df[df['packet_loss_percent'] > 0]['round_id'].unique()
if len(failure_rounds) > 0:
    print(f"Failures occurred in rounds: {sorted(failure_rounds)[:20]}")
    print(f"Total rounds with failures: {len(failure_rounds)} out of {df['round_id'].max()}")
else:
    print("[NOTE] No failures detected - run collection again and create more interference")

# Show first few rows
print("\n" + "="*60)
print("SAMPLE DATA (first 10 rows)")
print("="*60)
print(df.head(10).to_string())

print("\n" + "="*60)
print("NEXT STEPS")
print("="*60)
if len(failures) > 5:
    print("[OK] You have enough failure data!")
    print("-> Run 03_label_data.py next")
else:
    print("[WARNING] Very few failures detected.")
    print("-> Run data collection again and:")
    print("   1. Walk farther from router")
    print("   2. Start a large download")
    print("   3. Stream 4K video on another device")