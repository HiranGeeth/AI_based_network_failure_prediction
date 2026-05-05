# 05_predict_live.py - Real-time failure prediction using trained model
import time
import subprocess
import re
import pandas as pd
import numpy as np
import joblib
import os
import platform
from collections import deque
from datetime import datetime

print("="*70)
print("LIVE FAILURE PREDICTION SYSTEM")
print("="*70)

# Load trained model
model_folder = "models"
model_files = [f for f in os.listdir(model_folder) if f.startswith('failure_predictor_') and f.endswith('.pkl')]

if not model_files:
    print("[ERROR] No trained model found!")
    print("Run 04_train_model.py first")
    exit()

# Get the latest model
latest_model = max(model_files, key=lambda x: os.path.getctime(os.path.join(model_folder, x)))
model_path = os.path.join(model_folder, latest_model)
feature_path = os.path.join(model_folder, 'feature_columns.pkl')

print(f"\n[LOADING] Model: {latest_model}")
model = joblib.load(model_path)
feature_columns = joblib.load(feature_path)
print(f"[OK] Model loaded successfully")
print(f"[OK] Expects {len(feature_columns)} features")

# Configuration - CHANGE THIS TO YOUR ROUTER IP
ROUTER_IP = "10.34.15.254" 
DNS_IP = "8.8.8.8"
CHECK_INTERVAL = 10  
HISTORY_SIZE = 10

# Data storage for rolling features
history = {
    'router_ping': deque(maxlen=HISTORY_SIZE),
    'dns_ping': deque(maxlen=HISTORY_SIZE),
    'rssi': deque(maxlen=HISTORY_SIZE),
    'timestamp': deque(maxlen=HISTORY_SIZE)
}

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
            return float(rssi_match.group(1))
        
        # Fall back to percentage
        perc_match = re.search(r'Signal\s*:\s*(\d+)%', output)
        if perc_match:
            percentage = int(perc_match.group(1))
            return float(-100 + (percentage * 0.6))
        
        return -100.0
    except Exception:
        return -100.0

def ping_target(ip_address):
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
            # Check for timeout or unreachable
            if "unreachable" in output.lower() or "timed out" in output.lower():
                return 9999.0
            return 9999.0
    except subprocess.TimeoutExpired:
        return 9999.0
    except Exception:
        return 9999.0

def get_features():
    """Extract features from history for prediction"""
    if len(history['router_ping']) < 5:
        return None
    
    # Create lists for recent values
    router_list = list(history['router_ping'])
    dns_list = list(history['dns_ping'])
    rssi_list = list(history['rssi'])
    
    # Calculate features
    features = {
        'router_ping_ms': router_list[-1],
        'dns_ping_ms': dns_list[-1],
        'rssi_dbm': rssi_list[-1],
        'router_ping_rolling5': np.mean(router_list[-5:]),
        'dns_ping_rolling5': np.mean(dns_list[-5:]),
        'rssi_rolling5': np.mean(rssi_list[-5:]),
        'router_trend': router_list[-1] - router_list[-5] if len(router_list) >= 5 else 0,
        'dns_trend': dns_list[-1] - dns_list[-5] if len(dns_list) >= 5 else 0,
        'rssi_trend': rssi_list[-1] - rssi_list[-5] if len(rssi_list) >= 5 else 0
    }
    
    # Return in correct order
    return [features[col] for col in feature_columns]

def get_status(minutes):
    """Get status based on predicted minutes"""
    if minutes < 2:
        return "CRITICAL", "!"
    elif minutes < 5:
        return "WARNING", "!"
    elif minutes < 8:
        return "DEGRADING", "-"
    else:
        return "HEALTHY", " "

def clear_screen():
    """Clear console for live updates"""
    os.system('cls' if platform.system().lower() == 'windows' else 'clear')

print(f"\n[STARTING] Real-time network monitor")
print(f"[TARGET] Router: {ROUTER_IP}")
print(f"[TARGET] DNS: {DNS_IP}")
print(f"[INTERVAL] Every {CHECK_INTERVAL} seconds")
print(f"[HISTORY] Need 5 readings for prediction")
print("\nPress Ctrl+C to stop\n")

time.sleep(2)

# Main monitoring loop
round_count = 0

try:
    while True:
        round_count += 1
        
        # Collect current data
        router_ping = ping_target(ROUTER_IP)
        dns_ping = ping_target(DNS_IP)
        rssi = get_wifi_rssi()
        
        # Store in history
        history['router_ping'].append(router_ping)
        history['dns_ping'].append(dns_ping)
        history['rssi'].append(rssi)
        history['timestamp'].append(datetime.now())
        
        # Clear screen every 5 rounds for clean display
        if round_count % 5 == 0:
            clear_screen()
            print("="*70)
            print("LIVE FAILURE PREDICTION SYSTEM")
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Round: {round_count} | Readings: {len(history['router_ping'])}/10")
            print("="*70)
            print("")
        
        # Get prediction
        features = get_features()
        
        # Display current readings
        print(f"[CURRENT NETWORK STATE]")
        print(f"  Router Ping: {router_ping:.0f} ms")
        print(f"  DNS Ping:    {dns_ping:.0f} ms")
        print(f"  RSSI:        {rssi:.1f} dBm")
        print("")
        
        # Make prediction if enough history
        if features is not None:
            prediction = model.predict([features])[0]
            status, symbol = get_status(prediction)
            
            print(f"[PREDICTION]")
            print(f"  Minutes to failure: {prediction:.1f}")
            print(f"  Status: {status} {symbol}")
            print("")
            
            # Alert for critical failures
            if prediction < 2:
                print("="*70)
                print("  CRITICAL WARNING - Failure Imminent!")
                print(f"  Expected failure within {prediction:.0f} minutes")
                print("  Action: Move closer to router or restart network")
                print("="*70)
                print("")
            elif prediction < 5:
                print("-"*70)
                print(f"  WARNING - Degradation detected")
                print(f"  Expected failure in {prediction:.0f} minutes")
                print("-"*70)
                print("")
            
            # Show trend analysis
            if len(history['dns_ping']) >= 5:
                dns_trend = history['dns_ping'][-1] - history['dns_ping'][-5]
                if dns_trend > 50:
                    print(f"[TREND] DNS latency INCREASING (+{dns_trend:.0f}ms in last 5 readings)")
                elif dns_trend < -50:
                    print(f"[TREND] DNS latency DECREASING (recovering)")
                
                rssi_trend = history['rssi'][-1] - history['rssi'][-5]
                if rssi_trend < -5:
                    print(f"[TREND] Signal STRENGTH DROPPING ({rssi_trend:.0f}dBm)")
                elif rssi_trend > 5:
                    print(f"[TREND] Signal IMPROVING (+{rssi_trend:.0f}dBm)")
        else:
            print(f"[PREDICTION] Waiting for data... ({len(history['router_ping'])}/5 readings)")
            print("")
        
        # Simple health indicators
        print(f"[HEALTH INDICATORS]")
        if router_ping < 50 and dns_ping < 100:
            print("  [OK] Low latency")
        elif router_ping > 200 or dns_ping > 200:
            print("  [WARN] High latency detected")
        
        if rssi > -60:
            print("  [OK] Strong signal")
        elif rssi > -70:
            print("  [WARN] Moderate signal")
        elif rssi > -80:
            print("  [WARN] Weak signal")
        else:
            print("  [CRITICAL] Very weak signal")
        
        # Next check
        print(f"\n[Next check in {CHECK_INTERVAL} seconds...]")
        
        time.sleep(CHECK_INTERVAL)
        
except KeyboardInterrupt:
    print("\n" + "="*70)
    print("[STOPPED] Live monitoring ended")
    print(f"[SUMMARY] Completed {round_count} monitoring rounds")
    
    if len(history['router_ping']) > 0:
        print(f"\nSession Statistics:")
        print(f"  Avg Router Ping: {np.mean(list(history['router_ping'])):.0f} ms")
        print(f"  Avg DNS Ping: {np.mean(list(history['dns_ping'])):.0f} ms")
        print(f"  Avg RSSI: {np.mean(list(history['rssi'])):.1f} dBm")
    print("="*70)