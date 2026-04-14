# 00_test_network.py
import subprocess
import platform

def test_ping(ip_address, name):
    print(f"\n--- Testing {name} ({ip_address}) ---")
    
    # Different command for Windows vs Mac/Linux
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    cmd = ['ping', param, '3', ip_address]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        print(result.stdout)
        
        if "Destination host unreachable" in result.stdout or "Request timed out" in result.stdout:
            print(f" Cannot reach {name}")
            return False
        else:
            print(f" Successfully reached {name}")
            return True
    except Exception as e:
        print(f" Error: {e}")
        return False


MY_ROUTER_IP = "192.168.1.1" 

# Test both targets
router_works = test_ping(MY_ROUTER_IP, "Router")
dns_works = test_ping("8.8.8.8", "Google DNS")

print("\n" + "="*40)
if router_works and dns_works:
    print(" SUCCESS! Your computer can reach both targets.")
else:
    print(" FAILURE: Check your internet connection and router IP.")