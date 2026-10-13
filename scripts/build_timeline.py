#!/usr/bin/env python3
import argparse
import json
import os
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

TARGET_SR = 48000

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def stamp(seconds: float, srt=False) -> str:
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    sep = "," if srt else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{ms:03d}"


def read_voice(path: Path):
    data, sr = sf.read(path, always_2d=True, dtype="float32")
    mono = data.mean(axis=1)
    if sr != TARGET_SR:
        ratio = Fraction(TARGET_SR, sr).limit_denominator()
        mono = resample_poly(mono, ratio.numerator, ratio.denominator).astype(np.float32)
    return mono


def main() -> None:
    parser = argparse.ArgumentParser(description="按旁白实际长度生成统一时间轴")
    parser.add_argument("project", type=Path)
    parser.add_argument("--lead", type=float, default=0.12)
    parser.add_argument("--gap", type=float, default=0.30)
    args = parser.parse_args()
    project = Path(os.path.abspath(args.project))
    source = json.loads((project / "narration.json").read_text(encoding="utf-8"))
    lines = source.get("lines", [])
    if not lines:
        raise SystemExit("narration.json 里没有旁白句子。")

    cursor = 0.0
    timeline = []
    audio_parts = []
    silence = lambda seconds: np.zeros(round(seconds * TARGET_SR), dtype=np.float32)
    for index, item in enumerate(lines, 1):
        line_id = str(item.get("id") or f"{index:03d}")
        wav_path = project / "audio/voice" / f"{line_id}.wav"
        if not wav_path.exists():
            raise SystemExit(f"缺少旁白：{wav_path}")
        voice = read_voice(wav_path)
        audio_parts.append(silence(args.lead))
        start = cursor + args.lead
        end = start + len(voice) / TARGET_SR
        timeline.append({
            "id": line_id,
            "text": item["text"],
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(len(voice) / TARGET_SR, 3),
            "audio": f"audio/voice/{line_id}.wav",
        })
        audio_parts.extend([voice, silence(args.gap)])
        cursor = end + args.gap

    joined = np.concatenate(audio_parts) if audio_parts else np.zeros(1, dtype=np.float32)
    sf.write(project / "audio/narration.wav", joined, TARGET_SR, subtype="PCM_16")
    payload = {"sample_rate": TARGET_SR, "duration": round(len(joined) / TARGET_SR, 3), "lines": timeline}
    (project / "timeline.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    srt = []
    for index, item in enumerate(timeline, 1):
        srt.extend([str(index), f"{stamp(item['start'], True)} --> {stamp(item['end'], True)}", item["text"], ""])
    (project / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")

    subs = [{"a": item["start"], "b": item["end"], "zh": item["text"]} for item in timeline]
    js = (
        f"window.GENERATED_DURATION = {payload['duration']};\n"
        + "window.GENERATED_SUBS = "
        + json.dumps(subs, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (project / "generated_subs.js").write_text(js, encoding="utf-8")
    print(f"timeline: {len(timeline)} lines, {payload['duration']:.2f}s")


if __name__ == "__main__":
    main()
