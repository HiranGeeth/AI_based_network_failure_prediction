# Testing all 5 telecom parameters

import subprocess
import re
import time
import platform

print("="*70)
print("ADVANCED NETWORK TEST - Telecom Parameters")
print("="*70)
print("Testing ability to collect:\n")
print("  1. Router Ping Latency")
print("  2. DNS Ping Latency")
print("  3. RSSI (dBm)")
print("  4. Noise Floor (dBm)")
print("  5. TX Rate (Mbps)")
print("="*70)

# Configuration
ROUTER_IP = "10.34.15.254" 
DNS_IP = "8.8.8.8"

def test_ping(ip_address, name):
    """Test ping and return latency in ms"""
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
            latency = float(match.group(1))
            print(f"   {name} Ping: {latency:.0f}ms")
            return latency
        else:
            print(f"   {name} Ping: FAILED")
            return None
    except Exception as e:
        print(f"   {name} Ping: ERROR - {e}")
        return None

def get_wifi_advanced_stats():
    """Get RSSI, Noise, TX Rate from Windows WiFi adapter"""
    
    if platform.system().lower() != 'windows':
        print("\n  ⚠️ This script is optimized for Windows")
        print("  RSSI/Noise/TX Rate collection only works on Windows\n")
        return None
    
    stats = {}
    
    try:
        # Run netsh command
        result = subprocess.run(
            ['netsh', 'wlan', 'show', 'interfaces'],
            capture_output=True, text=True, shell=True
        )
        output = result.stdout
        
        print("\n" + "-"*50)
        print("RAW NETSH OUTPUT (for debugging):")
        print("-"*50)
        # Show relevant lines
        for line in output.split('\n'):
            if any(keyword in line for keyword in ['Signal', 'Noise', 'Rate', 'Channel', 'Radio']):
                print(f"  {line.strip()}")
        print("-"*50 + "\n")
        
        # Parse RSSI (percentage or dBm)
        # Try to get dBm directly first
        rssi_dbm_match = re.search(r'Signal\s*:\s*(-\d+)\s*dBm', output)
        if rssi_dbm_match:
            stats['rssi_dbm'] = int(rssi_dbm_match.group(1))
            print(f"  ✓ RSSI: {stats['rssi_dbm']} dBm (native)")
        else:
            # Fall back to percentage
            rssi_perc_match = re.search(r'Signal\s*:\s*(\d+)%', output)
            if rssi_perc_match:
                percentage = int(rssi_perc_match.group(1))
                # Convert percentage to approximate dBm
                stats['rssi_dbm'] = round(-100 + (percentage * 0.6), 1)
                print(f"   RSSI: {stats['rssi_dbm']} dBm (converted from {percentage}%)")
            else:
                print(f"   RSSI: NOT FOUND")
                stats['rssi_dbm'] = None
        
        # Parse Noise Floor
        noise_match = re.search(r'Noise\s*:\s*(-\d+)', output)
        if noise_match:
            stats['noise_dbm'] = int(noise_match.group(1))
            print(f"   Noise Floor: {stats['noise_dbm']} dBm")
        else:
            print(f"   Noise Floor: NOT FOUND (some drivers don't expose this)")
            stats['noise_dbm'] = None
        
        # Parse TX Rate (Mbps)
        tx_rate_match = re.search(r'Transmit rate\s*:\s*(\d+)', output)
        if tx_rate_match:
            stats['tx_rate_mbps'] = int(tx_rate_match.group(1))
            print(f"   TX Rate: {stats['tx_rate_mbps']} Mbps")
        else:
            # Try receive rate as fallback
            rx_rate_match = re.search(r'Receive rate\s*:\s*(\d+)', output)
            if rx_rate_match:
                stats['tx_rate_mbps'] = int(rx_rate_match.group(1))
                print(f"   TX Rate: {stats['tx_rate_mbps']} Mbps (using Receive rate)")
            else:
                print(f"   TX Rate: NOT FOUND")
                stats['tx_rate_mbps'] = None
        
        # Additional useful info
        channel_match = re.search(r'Channel\s*:\s*(\d+)', output)
        if channel_match:
            stats['channel'] = int(channel_match.group(1))
            print(f"    Channel: {stats['channel']}")
        
        radio_match = re.search(r'Radio type\s*:\s*(.+)', output)
        if radio_match:
            stats['radio_type'] = radio_match.group(1).strip()
            print(f"    Radio Type: {stats['radio_type']}")
        
    except Exception as e:
        print(f"   ERROR collecting WiFi stats: {e}")
        return None
    
    return stats

def calculate_snr(rssi_dbm, noise_dbm):
    """Calculate Signal-to-Noise Ratio"""
    if rssi_dbm is not None and noise_dbm is not None:
        snr = rssi_dbm - noise_dbm
        print(f"\n   Calculated SNR: {snr:.0f} dB")
        
        # Quality assessment
        if snr > 25:
            print(f"     → Excellent signal quality")
        elif snr > 15:
            print(f"     → Good signal quality")
        elif snr > 10:
            print(f"     → Fair signal quality")
        else:
            print(f"     → Poor signal quality (failure risk)")
        return snr
    return None

def test_failure_scenario():
    """Simple test to show how parameters change"""
    print("\n" + "="*70)
    print("FAILURE SCENARIO TEST")
    print("="*70)
    print("To see how parameters change during degradation:")
    print("  1. Walk to the farthest room from your router")
    print("  2. Start a large download or YouTube video")
    print("  3. Observe how RSSI drops and TX rate decreases")
    print("\nPress Enter when ready to start 30-second monitoring...")
    input()
    
    print("\n" + "="*50)
    print("MONITORING (30 seconds)...")
    print("="*50)
    
    for i in range(3):
        print(f"\n--- Sample {i+1} ---")
        
        # Get ping
        router_lat = test_ping(ROUTER_IP, "Router")
        dns_lat = test_ping(DNS_IP, "DNS")
        
        # Get WiFi stats
        wifi_stats = get_wifi_advanced_stats()
        
        if wifi_stats:
            print(f"\n   RF Metrics:")
            print(f"     RSSI: {wifi_stats.get('rssi_dbm', 'N/A')} dBm")
            print(f"     Noise: {wifi_stats.get('noise_dbm', 'N/A')} dBm")
            print(f"     TX Rate: {wifi_stats.get('tx_rate_mbps', 'N/A')} Mbps")
            
            if wifi_stats.get('rssi_dbm') and wifi_stats.get('noise_dbm'):
                calculate_snr(wifi_stats['rssi_dbm'], wifi_stats['noise_dbm'])
        
        if i < 2:
            print("\n  Waiting 10 seconds...")
            time.sleep(10)
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)

def main():
    # Step 1: Verify router IP
    print("\n[STEP 1] Testing connectivity...")
    print(f"Router IP: {ROUTER_IP}")
    print(f"DNS IP: {DNS_IP}\n")
    
    router_ok = test_ping(ROUTER_IP, "Router")
    dns_ok = test_ping(DNS_IP, "DNS")
    
    if not router_ok and not dns_ok:
        print("\n No network connectivity!")
        print("   Check your router IP and internet connection")
        return
    
    # Step 2: Get WiFi stats
    print("\n[STEP 2] Reading WiFi adapter statistics...")
    wifi_stats = get_wifi_advanced_stats()
    
    # Step 3: Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    
    parameters = {
        "Router Ping Latency": router_ok is not None,
        "DNS Ping Latency": dns_ok is not None,
        "RSSI (dBm)": wifi_stats and wifi_stats.get('rssi_dbm') is not None,
        "Noise Floor (dBm)": wifi_stats and wifi_stats.get('noise_dbm') is not None,
        "TX Rate (Mbps)": wifi_stats and wifi_stats.get('tx_rate_mbps') is not None,
    }
    
    all_available = True
    for param, available in parameters.items():
        status = " AVAILABLE" if available else " NOT AVAILABLE"
        print(f"  {param}: {status}")
        if not available:
            all_available = False
    
    print("\n" + "="*70)
    
    if all_available:
        print(" SUCCESS! All 5 parameters are available!")
        print("\nYou can now use these for your AI model:")
        print("  1. Router Ping → Local network health")
        print("  2. DNS Ping → Internet health")
        print("  3. RSSI → Signal strength")
        print("  4. Noise Floor → Interference level")
        print("  5. TX Rate → Link quality")
        print("\n Extra: SNR (Signal-to-Noise Ratio) can be calculated from RSSI + Noise")
    else:
        print(" Some parameters are not available on your adapter/driver")
        print("  - Noise Floor is often hidden on consumer Intel WiFi 4 cards")
        print("  - You may need to upgrade drivers or use a different adapter")
    
    # Optional: Run failure scenario test
    print("\n" + "="*70)
    response = input("Run failure scenario test? (y/n): ")
    if response.lower() == 'y':
        test_failure_scenario()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()