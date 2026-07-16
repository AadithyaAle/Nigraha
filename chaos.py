import random
import time

from app_paths import DEFAULT_LOG_FILE

LOG_FILE = DEFAULT_LOG_FILE
ERRORS = [
    "CRITICAL: Kernel Panic - Memory Segment Violation at 0x004F",
    "ERROR: PostgreSQL Service failed to start (Port 5432 in use)",
    "ERROR: NVRM: API mismatch: NVIDIA Driver 535 vs Kernel Module 525",
    "CRITICAL: Thermal Throttling detected! CPU Temp > 95C",
    "ERROR: wifi_adapter_0: Hardware Interface Unreachable",
]


def main():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"🔥 CHAOS GENERATOR INITIATED on {LOG_FILE}")
    print("Press Ctrl+C to stop burning the system...")

    try:
        while True:
            disaster = random.choice(ERRORS)
            with open(LOG_FILE, "a", encoding="utf-8") as handle:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                handle.write(f"[{timestamp}] {disaster}\n")
            print(f"💥 Injected: {disaster}")
            time.sleep(random.randint(5, 10))
    except KeyboardInterrupt:
        print("\n🧯 Chaos Extinguished.")


if __name__ == "__main__":
    main()
