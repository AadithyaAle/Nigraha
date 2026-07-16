import platform
import psutil
import json
import shutil
import os
from datetime import datetime

# Safe Import for Linux Distro Info
try:
    import distro
    LINUX_DISTRO = distro.name(pretty=True)
except ImportError:
    LINUX_DISTRO = "Linux (Unknown Distro)"

# Safe Import for NVIDIA GPU
try:
    import GPUtil
    HAS_GPU = True
except ImportError:
    HAS_GPU = False

def get_system_report():
    print("🔍 Scanning System Hardware...")
    
    # 1. OS Details
    os_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "distro": LINUX_DISTRO if platform.system() == "Linux" else "N/A"
    }

    # 2. CPU & RAM
    hardware = {
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_total_threads": psutil.cpu_count(logical=True),
        "cpu_usage_percent": psutil.cpu_percent(interval=1),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "ram_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
        "ram_used_percent": psutil.virtual_memory().percent
    }

    # 3. GPU (NVIDIA Only)
    gpu_info = []
    if HAS_GPU:
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_info.append({
                    "name": gpu.name,
                    "memory_total": f"{gpu.memoryTotal}MB",
                    "memory_used": f"{gpu.memoryUsed}MB",
                    "temperature": f"{gpu.temperature} C",
                    "load": f"{gpu.load*100}%"
                })
        except Exception:
            gpu_info.append({"error": "GPU detected but querying failed"})
    else:
        gpu_info.append({"info": "No NVIDIA GPU detected or GPUtil not installed"})

    # 4. Critical Tools Check
    tools = {
        "python": platform.python_version(),
        "pip": shutil.which("pip") is not None,
        "git": shutil.which("git") is not None,
        "docker": shutil.which("docker") is not None,
        "nvidia-smi": shutil.which("nvidia-smi") is not None,
    }

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "os": os_info,
        "hardware": hardware,
        "gpu": gpu_info,
        "installed_tools": tools
    }

    return report

if __name__ == "__main__":
    # Test Run
    print(json.dumps(get_system_report(), indent=4))