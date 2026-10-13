import shutil
import os
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parent.parent


def ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = [
        ROOT / ".runtime/ffmpeg/bin/ffmpeg.exe",
        ROOT / ".runtime/ffmpeg/ffmpeg.exe",
        Path.home() / "AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise SystemExit("找不到 FFmpeg。请运行 scripts/setup-ffmpeg.ps1。")
