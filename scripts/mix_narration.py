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
    parser.add_argument("--bgm-db", type=float, default=-18.0,
                        help="外部 BGM 增益；默认 -18 dB")
    parser.add_argument("--score-db", type=float, default=-6.5,
                        help="合成背景音乐与事件音增益；默认 -6.5 dB，保持可听")
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
    if not score.exists():
        raise SystemExit(
            f"缺少全程背景音乐：{score}。请先运行 engine/audio.py <工程> --wav-only。"
        )
    if args.bgm_db > -14:
        raise SystemExit("为避免盖住旁白，--bgm-db 不能高于 -14 dB。建议保留默认 -18 dB。")
    if args.score_db > -4.5:
        raise SystemExit("为避免事件音和底乐盖住旁白，--score-db 不能高于 -4.5 dB。")

    cmd = [ffmpeg(), "-v", "error", "-y", "-i", str(raw), "-i", str(narration)]
    background_indices = []
    cmd += ["-i", str(score)]
    background_indices.append((2, args.score_db))
    if args.bgm:
        if not args.bgm.exists():
            raise SystemExit(f"找不到 BGM：{args.bgm}")
        cmd += ["-stream_loop", "-1", "-i", str(args.bgm)]
        background_indices.append((3, args.bgm_db))

    if background_indices:
        pieces = [
            "[1:a]aformat=channel_layouts=stereo,highpass=f=70,"
            "loudnorm=I=-16:TP=-2:LRA=7,asplit=2[voice_sc][voice_mix]"
        ]
        labels = []
        for n, (index, gain) in enumerate(background_indices):
            pieces.append(f"[{index}:a]volume={gain}dB[bg{n}]")
            labels.append(f"[bg{n}]")
        if len(labels) > 1:
            pieces.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0[bg]")
        else:
            pieces.append(f"{labels[0]}anull[bg]")
        # 人声出现时背景平滑下压；停顿时缓慢回升，避免忽大忽小。
        pieces.append(
            "[bg][voice_sc]sidechaincompress="
            "threshold=0.02:ratio=5.5:attack=18:release=550[ducked]"
        )
        pieces.append("[voice_mix][ducked]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        filter_graph = ";".join(pieces)
    else:
        filter_graph = "[1:a]aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11[a]"

    cmd += [
        "-filter_complex", filter_graph,
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart", str(output),
    ]
    subprocess.run(cmd, check=True)
    print(output)


if __name__ == "__main__":
    main()
