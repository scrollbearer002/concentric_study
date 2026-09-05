"""Hardware profiling for local-model fitness ranking."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HardwareProfile:
    chip: str
    os_label: str
    arch: str
    cores: int
    memory_gb: float
    accel: str
    unified_memory: bool = False

    def summary_line(self) -> str:
        mem_label = f"{self.memory_gb:g} GB unified" if self.unified_memory else f"{self.memory_gb:g} GB RAM"
        return f"{self.chip} · {self.os_label} {self.arch} · {self.cores} cores · {mem_label} · {self.accel}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _memory_gb() -> float:
    try:
        import psutil

        return round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return round((pages * page_size) / (1024**3), 1)
        except Exception:
            return 8.0


def _cpu_cores() -> int:
    return os.cpu_count() or 1


def _detect_apple_chip() -> str | None:
    if platform.system() != "Darwin":
        return None
    try:
        brand = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            text=True,
            timeout=2,
        ).strip()
        if brand:
            return brand.replace("Apple ", "")
    except Exception:
        pass
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "Apple Silicon"
    return None


def _detect_linux_chip() -> str:
    model = ""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("model name"):
                    model = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass
    if not model:
        model = platform.processor() or "CPU"
    # Compact Xeon / Intel names for the status line
    if "Xeon" in model:
        return "Intel Xeon"
    if model.startswith("Intel(R)"):
        parts = model.replace("(R)", "").replace("CPU", "").split("@")[0].strip()
        return parts[:40]
    return model[:40]


def _detect_accel(system: str, arch: str) -> str:
    if system == "Darwin" and arch in {"arm64", "aarch64"}:
        return "MTL"
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                text=True,
                timeout=3,
            ).strip()
            if out:
                return "CUDA"
        except Exception:
            return "CUDA"
    # CPU-only fallback labels matching Magnitude-style short tags
    if arch in {"arm64", "aarch64"}:
        return "NEON"
    return "CPU"


def profile_hardware() -> HardwareProfile:
    system = platform.system()
    arch = platform.machine()
    if arch == "x86_64":
        arch_label = "x86_64"
    elif arch in {"arm64", "aarch64"}:
        arch_label = "ARM64"
    else:
        arch_label = arch

    apple = _detect_apple_chip()
    if apple:
        chip = apple if apple.startswith("Apple") or apple.startswith("M") else f"Apple {apple}"
        if not chip.startswith("Apple") and chip.startswith("M"):
            chip = f"Apple {chip}"
        os_label = "macOS"
        unified = True
    else:
        chip = _detect_linux_chip() if system == "Linux" else platform.processor() or "CPU"
        os_label = "Linux" if system == "Linux" else system
        unified = False

    return HardwareProfile(
        chip=chip,
        os_label=os_label,
        arch=arch_label,
        cores=_cpu_cores(),
        memory_gb=_memory_gb(),
        accel=_detect_accel(system, arch),
        unified_memory=unified,
    )
