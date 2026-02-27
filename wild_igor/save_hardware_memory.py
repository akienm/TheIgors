"""
One-shot script: save Akien's hardware inventory to Igor's FACTUAL memory.
Run from TheIgors/wild_igor/ with the venv active.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from igor.memory.cortex import Cortex
from igor.memory.models import Memory, MemoryType

db_path = Path(__file__).parent / "data" / "wild-0001.db"
cortex = Cortex(db_path)

machines = [
    {
        "hostname": "akiendelllinux",
        "narrative": (
            "akiendelllinux — Dell Latitude 5310, Intel i7-10610U @ 1.80GHz (2304 MHz), "
            "4 cores / 8 logical processors, 32GB RAM, Intel Iris video (no GPU), "
            "IP 10.0.0.229. THIS IS ME — the machine Igor runs on."
        ),
        "metadata": {
            "hostname": "akiendelllinux",
            "model": "Dell Latitude 5310",
            "cpu": "i7-10610U @ 1.80GHz",
            "cores": "4c/8t",
            "ram_gb": 32,
            "video": "Intel Iris",
            "gpu": False,
            "ip": "10.0.0.229",
            "role": "Igor's host machine",
            "owner": "akienm",
        }
    },
    {
        "hostname": "akiendell",
        "narrative": (
            "akiendell — Dell Latitude 5310, Intel i7-10610U @ 1.80GHz (2304 MHz), "
            "4 cores / 8 logical processors, 32GB RAM, Intel Iris video (no GPU), "
            "IP 10.0.0.99. Akien's main daily workstation."
        ),
        "metadata": {
            "hostname": "akiendell",
            "model": "Dell Latitude 5310",
            "cpu": "i7-10610U @ 1.80GHz",
            "cores": "4c/8t",
            "ram_gb": 32,
            "video": "Intel Iris",
            "gpu": False,
            "ip": "10.0.0.99",
            "role": "Akien's main daily workstation",
            "owner": "akienm",
        }
    },
    {
        "hostname": "akienyogai7",
        "narrative": (
            "akienyogai7 — Lenovo Yoga 9th gen, Intel i7u, 16GB RAM, Intel video (no GPU). "
            "Drives the living room TV — it's the computer behind the living room display, "
            "not the TV's built-in system."
        ),
        "metadata": {
            "hostname": "akienyogai7",
            "model": "Lenovo Yoga 9th gen",
            "cpu": "i7u (9th gen)",
            "ram_gb": 16,
            "video": "Intel",
            "gpu": False,
            "role": "Living room TV's driving computer",
            "owner": "akienm",
        }
    },
    {
        "hostname": "akienyogai9",
        "narrative": (
            "akienyogai9 — Lenovo Yoga 11th gen, Intel i7, 16GB RAM. Bedroom TV computer."
        ),
        "metadata": {
            "hostname": "akienyogai9",
            "model": "Lenovo Yoga 11th gen",
            "cpu": "i7 (11th gen)",
            "ram_gb": 16,
            "role": "Bedroom TV computer",
            "owner": "akienm",
        }
    },
    {
        "hostname": "akienasus",
        "narrative": (
            "akienasus — ASUS laptop, 9th gen Intel i7, 20GB RAM, no GPU. "
            "Currently has no hard drive, but has a 512GB drive that can be installed."
        ),
        "metadata": {
            "hostname": "akienasus",
            "model": "ASUS laptop",
            "cpu": "i7 (9th gen)",
            "ram_gb": 20,
            "gpu": False,
            "hdd": "no drive installed; 512GB available to install",
            "role": "Spare / standby",
            "owner": "akienm",
        }
    },
    {
        "hostname": "akienpi",
        "narrative": (
            "akienpi — Raspberry Pi 400, default/stock hardware."
        ),
        "metadata": {
            "hostname": "akienpi",
            "model": "Raspberry Pi 400",
            "hardware": "default/stock",
            "role": "Pi device",
            "owner": "akienm",
        }
    },
]

# Parent: root node for factual/environment knowledge
# We'll use the general root id "R001" or whatever exists — 
# actually we'll search for a suitable parent or just use None
print(f"Total memories before: {cortex.total_count()}")

for m in machines:
    mem = Memory(
        narrative=m["narrative"],
        memory_type=MemoryType.FACTUAL,
        metadata=m["metadata"],
        valence=0.3,
    )
    cortex.store(mem)
    print(f"  Stored [{mem.id}]: {m['hostname']}")

# Also write a ring memory note about this save
cortex.write_ring(
    "Saved Akien's full hardware inventory to FACTUAL memory: "
    "akiendelllinux (ME, 10.0.0.229), akiendell (10.0.0.99), "
    "akienyogai7 (living room), akienyogai9 (bedroom), "
    "akienasus (spare, no HD), akienpi (RPi 400)",
    category="hardware"
)

print(f"Total memories after: {cortex.total_count()}")
print("Ring memory updated.")
print("Done!")
