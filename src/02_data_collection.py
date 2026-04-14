# 01_data_collection_fast.py - Aggressive collection for failure examples
import time
import csv
import subprocess
import re
from datetime import datetime
import os
import sys

# ================= CONFIGURATION =================
ROUTER_IP = "192.168.1.1"
COLLECTION_MINUTES = 20  # 20 minutes of aggressive collection
WAIT_SECONDS = 2  # Only 2 seconds between rounds
DATA_FOLDER = "data\\raw"
# =================================================

def create_folders():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    print(f"[OK] Folder: {DATA_FOLDER}")

def get_wifi_rssi():
    try:
        cmd = ['netsh', 'wlan', 'show', 'interfaces']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
        match = re.search(r'Signal\s*:\s*(\d+)%', result.stdout)
        if match:
            signal_percent = int(match.group(1))
            rssi_dbm = -90 + (signal_percent * 0.6)
            return round(rssi_dbm, 1)
        return -60
    except:
        return -60

def ping(ip_address):
    """Faster ping - only 3 pings instead of 5"""
    try:
        cmd = ['ping', '-n', '3', '-w', '1000', ip_address]  # 3 pings, 1 sec timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, shell=True)
        output = result.stdout
        
        latency = 9999
        loss = 100
        success = False
        
        loss_match = re.search(r'\((\d+)% loss\)', output)
        if loss_match:
            loss = int(loss_match.group(1))
            success = loss < 50
        
        latency_match = re.search(r'Average = (\d+)ms', output)
        if latency_match:
            latency = float(latency_match.group(1))
        
        return latency, loss, success
        
    except:
        return 9999, 100, False

def create_artificial_load():
    """Create network load to force failures"""
    try:
        # Start a background ping flood (gentle)
        subprocess.Popen(['ping', '-n', '10', '-l', '1400', '8.8.8.8'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
    except:
        pass

def collect_data():
    print("="*70)
    print("AGGRESSIVE DATA COLLECTOR - For Failure Examples")
    print("="*70)
    
    create_folders()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(DATA_FOLDER, f'network_data_aggressive_{timestamp}.csv')
    
    print(f"Duration: {COLLECTION_MINUTES} minutes")
    print(f"Wait time: {WAIT_SECONDS} seconds between rounds")
    print(f"Saving to: {output_file}")
    
   
    print("\nStarting in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    print("\n[RECORDING] Data collection ACTIVE\n")
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'timestamp', 'target', 'latency_ms', 'packet_loss_percent',
                'rssi_dbm', 'success', 'round_id'
            ])
            
            start_time = time.time()
            end_time = start_time + (COLLECTION_MINUTES * 60)
            round_counter = 0
            failure_rounds = 0
            
            while time.time() < end_time:
                round_counter += 1
                current_rssi = get_wifi_rssi()
                current_time = datetime.now().isoformat()
                
                elapsed = time.time() - start_time
                remaining = (COLLECTION_MINUTES * 60) - elapsed
                minutes_left = int(remaining // 60)
                seconds_left = int(remaining % 60)
                
                # Test Router
                router_latency, router_loss, router_success = ping(ROUTER_IP)
                writer.writerow([
                    current_time, 'router', router_latency, router_loss,
                    current_rssi, router_success, round_counter
                ])
                
                # Test DNS
                dns_latency, dns_loss, dns_success = ping("8.8.8.8")
                writer.writerow([
                    current_time, 'dns', dns_latency, dns_loss,
                    current_rssi, dns_success, round_counter
                ])
                
                # Count failures for this round
                round_failures = 0
                if router_loss > 0 or dns_loss > 0:
                    round_failures = 1
                    failure_rounds += 1
                
                # Visual status
                if router_loss == 0 and dns_loss == 0:
                    status = "[OK]"
                elif router_loss < 30 or dns_loss < 30:
                    status = "[WARN]"
                else:
                    status = "[FAIL]"
                
                print(f"[ROUND {round_counter:3d}] {status} Router: {router_loss:2d}% loss/{router_latency:3.0f}ms | DNS: {dns_loss:2d}% loss/{dns_latency:3.0f}ms | Time: {minutes_left:2d}:{seconds_left:02d}")
                
                # Short wait (2-3 seconds)
                time.sleep(WAIT_SECONDS)
                
                # Every 10 rounds, give a reminder
                if round_counter % 10 == 0:
                    print(f"  [TIP] Keep moving! Current failure rate: {failure_rounds}/{round_counter} ({failure_rounds*100//round_counter}%)")
                    print(f"  {'-'*60}")
            
            print("\n" + "="*70)
            print("[COMPLETE] Data collection finished!")
            print(f"[STATS] Total rounds: {round_counter}")
            print(f"[STATS] Rounds with failures: {failure_rounds} ({failure_rounds*100//round_counter}%)")
            print(f"[FILE] {output_file}")
            
            if failure_rounds < round_counter * 0.3:
                print("\n[WARNING] Low failure rate! Next time:")
                print("  - Move to a DIFFERENT room")
                print("  - Start a TORRENT download")
                print("  - Use your phone as a hotspot and connect through it")
            else:
                print("\n[SUCCESS] Good failure rate! Ready for training!")
            
            print("="*70)
            
    except KeyboardInterrupt:
        print(f"\n[STOPPED] Saved {round_counter} rounds")
        print(f"[FILE] {output_file}")
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    collect_data()