#!/usr/bin/env python3
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def yes(value):
    return "OK" if value else "MISSING"


def main() -> None:
    chrome = any(path.exists() for path in [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ])
    ffmpeg = (
        shutil.which("ffmpeg")
        or (ROOT / ".runtime/ffmpeg/bin/ffmpeg.exe").exists()
        or (Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe").exists()
    )
    print(f"Python {sys.version.split()[0]}: OK")
    print(f"Google Chrome: {yes(chrome)}")
    print(f"FFmpeg: {yes(ffmpeg)}")
    for package in ("numpy", "scipy", "PIL", "playwright", "soundfile"):
        print(f"{package}: {yes(importlib.util.find_spec(package))}")
    print(f"ChatTTS (preview only): {yes(importlib.util.find_spec('ChatTTS'))}")
    nvidia = shutil.which("nvidia-smi")
    if nvidia:
        result = subprocess.run(
            [nvidia, "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, check=False,
        )
        print("GPU:", result.stdout.strip() or "unknown")


if __name__ == "__main__":
    main()
