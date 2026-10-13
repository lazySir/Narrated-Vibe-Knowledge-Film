#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

from runtime import ffmpeg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="混合旁白、事件音和可选 BGM")
    parser.add_argument("project", type=Path)
    parser.add_argument("--bgm", type=Path)
    parser.add_argument("--bgm-db", type=float, default=-16.0)
    args = parser.parse_args()
    project = Path(os.path.abspath(args.project))
    raw = project / "renders/raw.mp4"
    narration = project / "audio/narration.wav"
    score = project / "audio/score.wav"
    output = project / "renders/final.mp4"
    if not raw.exists():
        raise SystemExit(f"缺少无声画面：{raw}")
    if not narration.exists():
        raise SystemExit(f"缺少旁白总轨：{narration}")

    cmd = [ffmpeg(), "-v", "error", "-y", "-i", str(raw), "-i", str(narration)]
    background_indices = []
    if score.exists():
        cmd += ["-i", str(score)]
        background_indices.append((2, -7.0))
    if args.bgm:
        if not args.bgm.exists():
            raise SystemExit(f"找不到 BGM：{args.bgm}")
        cmd += ["-stream_loop", "-1", "-i", str(args.bgm)]
        background_indices.append((2 + int(score.exists()), args.bgm_db))

    if background_indices:
        pieces = []
        labels = []
        for n, (index, gain) in enumerate(background_indices):
            pieces.append(f"[{index}:a]volume={gain}dB[bg{n}]")
            labels.append(f"[bg{n}]")
        if len(labels) > 1:
            pieces.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0[bg]")
        else:
            pieces.append(f"{labels[0]}anull[bg]")
        pieces.append("[bg][1:a]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[ducked]")
        pieces.append("[1:a][ducked]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        filter_graph = ";".join(pieces)
    else:
        filter_graph = "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]"

    cmd += [
        "-filter_complex", filter_graph,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", str(output),
    ]
    subprocess.run(cmd, check=True)
    print(output)


if __name__ == "__main__":
    main()
