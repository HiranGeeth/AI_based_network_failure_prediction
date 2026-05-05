# 02_data_collection.py - Collect Router Ping, DNS Ping, and RSSI
import time
import subprocess
import re
import pandas as pd
from datetime import datetime
import os
import platform

print("="*70)
print("DATA COLLECTION - Router Ping, DNS Ping, RSSI")
print("="*70)

# ================= CONFIGURATION =================
ROUTER_IP = "10.34.15.254"  # Your university gateway
DNS_IP = "8.8.8.8"
COLLECTION_MINUTES = 20  # Change to 5 for quick test
WAIT_SECONDS = 2  # Seconds between rounds
# =================================================

# Create data folder
DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Generate filename with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = os.path.join(DATA_FOLDER, f'network_data_{timestamp}.xlsx')

print(f"\n[CONFIG] Router IP: {ROUTER_IP}")
print(f"[CONFIG] DNS IP: {DNS_IP}")
print(f"[CONFIG] Duration: {COLLECTION_MINUTES} minutes")
print(f"[CONFIG] Interval: {WAIT_SECONDS} seconds between rounds")
print(f"[CONFIG] Output: {output_file}")
print("="*70)

def get_wifi_rssi():
    """Get WiFi RSSI in dBm from Windows"""
    try:
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'interfaces'],
            capture_output=True, text=True, shell=True
        )
        output = result.stdout
        
        # Try to get dBm directly
        rssi_match = re.search(r'Signal\s*:\s*(-\d+)\s*dBm', output)
        if rssi_match:
            return int(rssi_match.group(1))
        
        # Fall back to percentage
        perc_match = re.search(r'Signal\s*:\s*(\d+)%', output)
        if perc_match:
            percentage = int(perc_match.group(1))
            # Convert to approximate dBm
            return round(-100 + (percentage * 0.6), 1)
        
        return -100  # No signal
    except Exception as e:
        print(f"  [WARN] RSSI read error: {e}")
        return -100

def ping_target(ip_address, name):
    """Ping target and return latency in ms"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = ['ping', param, '3', ip_address]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout
        
        # Parse latency
        if platform.system().lower() == 'windows':
            match = re.search(r'Average = (\d+)ms', output)
        else:
            match = re.search(r'= [\d.]+/([\d.]+)/[\d.]+', output)
        
        if match:
            return float(match.group(1))
        else:
            # Check for "Destination unreachable" or "Request timed out"
            if "unreachable" in output.lower() or "timed out" in output.lower():
                return 9999
            return 9999
    except subprocess.TimeoutExpired:
        return 9999
    except Exception:
        return 9999

def calculate_rolling_features(df, window=5):
    """Calculate rolling averages and trends"""
    df['router_ping_rolling5'] = df['router_ping_ms'].rolling(window, min_periods=1).mean()
    df['dns_ping_rolling5'] = df['dns_ping_ms'].rolling(window, min_periods=1).mean()
    df['rssi_rolling5'] = df['rssi_dbm'].rolling(window, min_periods=1).mean()
    
    # Calculate trends (current - 5 rounds ago)
    df['router_trend'] = df['router_ping_ms'] - df['router_ping_ms'].shift(window)
    df['dns_trend'] = df['dns_ping_ms'] - df['dns_ping_ms'].shift(window)
    df['rssi_trend'] = df['rssi_dbm'] - df['rssi_dbm'].shift(window)
    
    # Fill NaN values (first few rows) with 0
    df['router_trend'] = df['router_trend'].fillna(0)
    df['dns_trend'] = df['dns_trend'].fillna(0)
    df['rssi_trend'] = df['rssi_trend'].fillna(0)
    
    return df

def add_labels(df, loss_threshold=200):
    """
    Add 'minutes_to_failure' labels based on high latency
    When latency > threshold, countdown begins
    """
    df['minutes_to_failure'] = 10  # Default healthy
    
    # Find rounds where router or DNS ping is high (failure indicator)
    high_latency_rounds = df[(df['router_ping_ms'] > loss_threshold) | 
                              (df['dns_ping_ms'] > loss_threshold)].index
    
    for idx in high_latency_rounds:
        # Look ahead up to 20 rounds
        lookahead_limit = min(idx + 20, len(df))
        remaining_minutes = 10
        for j in range(idx, lookahead_limit):
            # Linear decay from 10 to 0 minutes over lookahead window
            remaining_minutes = 10 * (1 - (j - idx) / 20)
            df.at[j, 'minutes_to_failure'] = max(0, min(10, remaining_minutes))
    
    return df

print("\n[STARTING] Data collection...")
print("Press Ctrl+C to stop early\n")

# Storage for data
data_rows = []
round_num = 0

try:
    start_time = time.time()
    end_time = start_time + (COLLECTION_MINUTES * 60)
    
    while time.time() < end_time:
        round_num += 1
        
        # Calculate elapsed and remaining time
        elapsed = time.time() - start_time
        remaining = end_time - time.time()
        minutes_left = int(remaining // 60)
        seconds_left = int(remaining % 60)
        
        # Collect data
        router_ping = ping_target(ROUTER_IP, "Router")
        dns_ping = ping_target(DNS_IP, "DNS")
        rssi = get_wifi_rssi()
        
        # Store
        data_rows.append({
            'round_id': round_num,
            'timestamp': datetime.now().isoformat(),
            'router_ping_ms': router_ping,
            'dns_ping_ms': dns_ping,
            'rssi_dbm': rssi
        })
        
        # Print progress
        status = "[OK]" if router_ping < 100 and dns_ping < 100 else "[WARN]"
        print(f"[ROUND {round_num:3d}] {status} Router: {router_ping:4.0f}ms | DNS: {dns_ping:4.0f}ms | RSSI: {rssi:5.1f}dBm | Time left: {minutes_left:2d}:{seconds_left:02d}")
        
        # Wait before next round
        time.sleep(WAIT_SECONDS)
    
except KeyboardInterrupt:
    print("\n\n[STOPPED] Data collection interrupted by user")
    print(f"[INFO] Saved {round_num} rounds")

finally:
    if data_rows:
        # Create DataFrame
        df = pd.DataFrame(data_rows)
        
        # Calculate rolling features
        df = calculate_rolling_features(df, window=5)
        
        # Add labels (minutes to failure)
        df = add_labels(df, loss_threshold=200)
        
        # Save to Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        
        print("\n" + "="*70)
        print("DATA COLLECTION COMPLETE")
        print("="*70)
        print(f"[STATS] Total rounds collected: {round_num}")
        print(f"[STATS] Total measurements: {round_num * 3} (ping router, ping dns, rssi)")
        print(f"[FILE] Saved to: {output_file}")
        
        # Show sample
        print("\n[PREVIEW] First 5 rows:")
        print(df[['round_id', 'router_ping_ms', 'dns_ping_ms', 'rssi_dbm', 
                  'router_ping_rolling5', 'minutes_to_failure']].head().to_string())
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("1. Run data collection multiple times with different network conditions")
        print("2. Then run 03_train_model.py to train your AI")
        print("="*70)
    else:
        print("[ERROR] No data collected!")