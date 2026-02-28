import subprocess, json

def get_gpu_stats() -> dict:
    """
    Dev machine  → queries nvidia-smi
    AMD production → swap to rocm-smi (same interface, zero code changes)
    """
    # NVIDIA (development)
    try:
        r = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,power.draw,temperature.gpu,"
             "utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            name, power, temp, usage, mem_used, mem_total = \
                [p.strip() for p in r.stdout.strip().split(',')]
            vram_pct = round(int(mem_used) / int(mem_total) * 100, 1)
            return {
                "name":     name,
                "power":    power,
                "temp":     temp,
                "usage":    usage,
                "vram":     str(vram_pct),
                "backend":  "nvidia-smi  ·  swap → rocm-smi for AMD production",
                "available": True
            }
    except Exception:
        pass

    # AMD ROCm (production target)
    try:
        r = subprocess.run(
            ["rocm-smi","--showpower","--showtemp","--showuse","--json"],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0:
            card = json.loads(r.stdout).get("card0", {})
            return {
                "name":    card.get("Card Series", "AMD Radeon GPU"),
                "power":   card.get("Average Graphics Package Power (W)", "N/A"),
                "temp":    card.get("Temperature (Sensor edge) (C)", "N/A"),
                "usage":   card.get("GPU Use (%)", "N/A"),
                "vram":    card.get("GPU Memory Use (%)", "N/A"),
                "backend": "rocm-smi (AMD production)",
                "available": True
            }
    except Exception:
        pass

    # Fallback
    return {
        "name":    "GPU (demo mode)",
        "power":   "72", "temp": "61",
        "usage":   "87", "vram": "56",
        "backend": "simulated",
        "available": False
    }
