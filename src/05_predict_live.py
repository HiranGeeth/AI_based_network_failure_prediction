# 05_predict_live.py - Real-time failure prediction
import time
import subprocess
import re
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime
from collections import deque
import platform

print("="*70)
print("LIVE FAILURE PREDICTION SYSTEM")
print("="*70)

# Load trained model
try:
    model = joblib.load('models/failure_predictor.pkl')
    feature_columns = joblib.load('models/feature_columns.pkl')
    print("[OK] Model loaded successfully")
except Exception as e:
    print(f"[ERROR] Cannot load model: {e}")
    print("Run 04_train_model.py first")
    exit()

# Configuration
ROUTER_IP = "192.168.1.1"
CHECK_INTERVAL = 10  # Seconds between predictions
HISTORY_SIZE = 10    # Keep last 10 readings for trends

# Data storage
history = {
    'router_latency': deque(maxlen=HISTORY_SIZE),
    'router_loss': deque(maxlen=HISTORY_SIZE),
    'dns_latency': deque(maxlen=HISTORY_SIZE),
    'dns_loss': deque(maxlen=HISTORY_SIZE),
    'timestamp': deque(maxlen=HISTORY_SIZE)
}

def get_wifi_rssi():
    """Get WiFi signal (if available)"""
    try:
        cmd = ['netsh', 'wlan', 'show', 'interfaces']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
        match = re.search(r'Signal\s*:\s*(\d+)%', result.stdout)
        if match:
            signal_percent = int(match.group(1))
            return -90 + (signal_percent * 0.6)
        return -60
    except:
        return -60

def ping_target(ip_address, count=3):
    """Fast ping for live monitoring"""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = ['ping', param, str(count), '-w', '1000', ip_address]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
        output = result.stdout
        
        loss = 100
        latency = 9999
        
        loss_match = re.search(r'\((\d+)% loss\)', output)
        if loss_match:
            loss = int(loss_match.group(1))
        
        latency_match = re.search(r'Average = (\d+)ms', output)
        if latency_match:
            latency = float(latency_match.group(1))
        
        return latency, loss
        
    except:
        return 9999, 100

def get_current_features():
    """Extract features from recent history for prediction"""
    if len(history['router_latency']) < 5:
        return None  # Not enough data yet
    
    # Create dataframe from recent history
    df_recent = pd.DataFrame({
        'router_latency_ms': list(history['router_latency']),
        'router_packet_loss_pct': list(history['router_loss']),
        'dns_latency_ms': list(history['dns_latency']),
        'dns_packet_loss_pct': list(history['dns_loss'])
    })
    
    # Calculate rolling features (last 5 readings)
    features = {
        'router_latency_ms': df_recent['router_latency_ms'].iloc[-1],
        'router_packet_loss_pct': df_recent['router_packet_loss_pct'].iloc[-1],
        'dns_latency_ms': df_recent['dns_latency_ms'].iloc[-1],
        'dns_packet_loss_pct': df_recent['dns_packet_loss_pct'].iloc[-1],
        'router_latency_ms_rolling5': df_recent['router_latency_ms'].tail(5).mean(),
        'dns_latency_ms_rolling5': df_recent['dns_latency_ms'].tail(5).mean(),
        'router_packet_loss_pct_rolling5': df_recent['router_packet_loss_pct'].tail(5).mean(),
        'dns_packet_loss_pct_rolling5': df_recent['dns_packet_loss_pct'].tail(5).mean(),
        'router_latency_trend': df_recent['router_latency_ms'].diff().mean(),
        'dns_latency_trend': df_recent['dns_latency_ms'].diff().mean(),
        'avg_latency': (df_recent['router_latency_ms'].iloc[-1] + df_recent['dns_latency_ms'].iloc[-1]) / 2
    }
    
    # Return in correct order
    return [features[col] for col in feature_columns]

def get_status_color(minutes_to_failure):
    """Convert prediction to status"""
    if minutes_to_failure < 2:
        return "CRITICAL", "red"
    elif minutes_to_failure < 5:
        return "WARNING", "yellow"
    elif minutes_to_failure < 8:
        return "DEGRADING", "green"
    else:
        return "HEALTHY", "white"

def clear_screen():
    """Clear console for live updates"""
    os.system('cls' if platform.system().lower() == 'windows' else 'clear')

print("\n[STARTING] Real-time monitor...")
print(f"[SETTINGS] Checking every {CHECK_INTERVAL} seconds")
print(f"[TARGET] Router: {ROUTER_IP}, DNS: 8.8.8.8")
print("\nPress Ctrl+C to stop\n")

time.sleep(2)

try:
    round_count = 0
    last_warning_time = 0
    
    while True:
        round_count += 1
        
        # Collect current data
        rssi = get_wifi_rssi()
        router_latency, router_loss = ping_target(ROUTER_IP)
        dns_latency, dns_loss = ping_target("8.8.8.8")
        
        # Store in history
        history['router_latency'].append(router_latency)
        history['router_loss'].append(router_loss)
        history['dns_latency'].append(dns_latency)
        history['dns_loss'].append(dns_loss)
        history['timestamp'].append(datetime.now())
        
        # Get prediction
        features = get_current_features()
        
        # Clear screen for live view (every 5 rounds to reduce flicker)
        if round_count % 5 == 0:
            clear_screen()
            print("="*70)
            print("LIVE FAILURE PREDICTION SYSTEM")
            print("="*70)
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Round: {round_count} | History: {len(history['router_latency'])} readings\n")
        
        # Display current readings
        print(f"[CURRENT NETWORK STATE]")
        print(f"  Router: {router_latency:4.0f}ms latency, {router_loss:3d}% loss")
        print(f"  DNS:    {dns_latency:4.0f}ms latency, {dns_loss:3d}% loss")
        print(f"  WiFi:   {rssi:.0f}dBm\n")
        
        # Make prediction if enough history
        if features is not None:
            prediction = model.predict([features])[0]
            status, color = get_status_color(prediction)
            
            print(f"[PREDICTION]")
            print(f"  Time to failure: {prediction:.1f} minutes")
            print(f"  Status: {status}")
            
            # Alert for critical failures
            if prediction < 2:
                print("\n" + "!"*70)
                print("  CRITICAL WARNING - Failure imminent!")
                print(f"   Expected failure within {prediction:.0f} minutes")
                print(f"   Take action: Move closer to router or restart network")
                print("!"*70 + "\n")
            elif prediction < 5:
                print(f"\n{'~'*70}")
                print(f"  Warning: Degradation detected")
                print(f"   Expected failure in {prediction:.0f} minutes")
                print(f"{'~'*70}\n")
            
            # Show trend
            if len(history['dns_latency']) >= 3:
                trend = history['dns_latency'][-1] - history['dns_latency'][-3]
                if trend > 50:
                    print(f"[TREND] DNS latency INCREASING rapidly (+{trend:.0f}ms in last 2 checks)")
                elif trend < -50:
                    print(f"[TREND] DNS latency DECREASING (recovering)")
        else:
            print(f"[PREDICTION] Waiting for more data... ({len(history['router_latency'])}/5 readings)")
        
        # Simple health indicators
        print(f"\n[HEALTH METRICS]")
        if router_loss == 0 and dns_loss == 0:
            print("   No packet loss detected")
        elif router_loss > 0 or dns_loss > 0:
            print(f"    Packet loss detected (Router: {router_loss}%, DNS: {dns_loss}%)")
        
        if dns_latency > 200:
            print(f"    High DNS latency ({dns_latency:.0f}ms)")
        elif dns_latency > 100:
            print(f"   Elevated DNS latency ({dns_latency:.0f}ms)")
        
        # Next check
        print(f"\n{'='*70}")
        print(f"Next check in {CHECK_INTERVAL} seconds... (Ctrl+C to stop)")
        
        time.sleep(CHECK_INTERVAL)
        
except KeyboardInterrupt:
    print("\n\n[STOPPED] Live monitoring ended")
    print(f"[SUMMARY] Completed {round_count} monitoring rounds")
    
    # Show final statistics
    if len(history['router_loss']) > 0:
        avg_router_loss = np.mean(history['router_loss'])
        avg_dns_loss = np.mean(history['dns_loss'])
        print(f"\nSession Statistics:")
        print(f"  Average Router Loss: {avg_router_loss:.1f}%")
        print(f"  Average DNS Loss: {avg_dns_loss:.1f}%")
        print(f"  Total checks: {round_count}")