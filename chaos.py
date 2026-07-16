import time
import random

LOG_FILE = "system_log.txt"

ERRORS = [
    "CRITICAL: Kernel Panic - Memory Segment Violation at 0x004F",
    "ERROR: PostgreSQL Service failed to start (Port 5432 in use)",
    "ERROR: NVRM: API mismatch: NVIDIA Driver 535 vs Kernel Module 525",
    "CRITICAL: Thermal Throttling detected! CPU Temp > 95C",
    "ERROR: wifi_adapter_0: Hardware Interface Unreachable"
]

print(f"🔥 CHAOS GENERATOR INITIATED on {LOG_FILE}")
print("Press Ctrl+C to stop burning the system...")

try:
    while True:
        # Pick a random disaster
        disaster = random.choice(ERRORS)
        
        with open(LOG_FILE, "a") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {disaster}\n"
            f.write(log_entry)
        
        print(f"💥 Injected: {disaster}")
        
        # Wait randomly between 5 to 10 seconds (so StackSentinel has time to react)
        time.sleep(random.randint(5, 10))

except KeyboardInterrupt:
    print("\n🧯 Chaos Extinguished.")