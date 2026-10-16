#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

from runtime import ffmpeg

ALLOWED = {"approved", "original", "public-domain"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def inspect_wav(path: Path, label: str):
    if not path.exists():
        return [f"缺少 {label}：{path.name}"]
    try:
        audio, _ = sf.read(path, dtype="float32")
    except Exception as exc:
        return [f"{label} 无法读取：{exc}"]
    if audio.size == 0:
        return [f"{label} 是空音频"]
    errors = []
    if not np.isfinite(audio).all():
        errors.append(f"{label} 含有非有限采样值")
    finite_audio = np.nan_to_num(audio)
    peak = float(np.max(np.abs(finite_audio)))
    dc = float(np.mean(finite_audio))
    if peak < 1e-5:
        errors.append(f"{label} 是全静音音频")
    if abs(dc) > 0.05:
        errors.append(f"{label} 存在异常直流偏移 {dc:.3f}")
    return errors


def wav_duration(path: Path):
    try:
        info = sf.info(path)
        return info.frames / info.samplerate if info.samplerate else 0.0
    except Exception:
        return 0.0


def inspect_video_audio(path: Path):
    if not path.exists():
        return [f"缺少 {path.name}"]
    result = subprocess.run(
        [
            ffmpeg(), "-hide_banner", "-nostats", "-i", str(path),
            "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return ["最终视频缺少可读取的音轨"]
    match = re.search(r"mean_volume:\s*(-?inf|[-\d.]+) dB", result.stderr)
    if not match or match.group(1) == "-inf" or float(match.group(1)) < -55:
        return ["最终视频音轨接近静音"]
    return []


def inspect(project: Path, require_video=True):
    errors = []
    project_json = json.loads((project / "project.json").read_text(encoding="utf-8"))
    manifest = json.loads((project / "license-manifest.json").read_text(encoding="utf-8"))
    usage = manifest.get("usage") or project_json.get("usage")
    if usage != project_json.get("usage"):
        errors.append("project.json 与 license-manifest.json 的 usage 不一致")
    assets = manifest.get("assets", [])
    if not assets:
        errors.append("license-manifest.json 没有任何素材记录")
    for index, asset in enumerate(assets, 1):
        name = asset.get("name") or f"第 {index} 项"
        status = asset.get("status", "unverified")
        if usage == "commercial" and status not in ALLOWED:
            errors.append(f"{name} 的许可状态是 {status}，不能用于商业发布")
        for field in ("kind", "name", "source", "license", "checked_on", "status"):
            if not str(asset.get(field, "")).strip():
                errors.append(f"{name} 缺少 {field}")

    generation = project / "audio/generation.json"
    if generation.exists():
        record = json.loads(generation.read_text(encoding="utf-8"))
        if usage == "commercial" and record.get("provider") == "cosyvoice3" and record.get("rights_confirmed") is not True:
            errors.append("CosyVoice3 的参考声音尚未确认拥有商业使用权")
        if usage == "commercial" and record.get("preview_only"):
            errors.append("商业工程仍在使用 preview-only 旁白")
    else:
        errors.append("缺少 audio/generation.json，无法确认旁白来源")

    for required in ("facts.md", "storyboard.md", "timeline.json", "subtitles.srt"):
        if not (project / required).exists():
            errors.append(f"缺少 {required}")
    publish = project / "publish.md"
    if not publish.exists():
        errors.append("缺少 publish.md，成片必须附带发布简介")
    else:
        publish_text = publish.read_text(encoding="utf-8").strip()
        if len(publish_text) < 40:
            errors.append("publish.md 内容太短，尚未形成可发布的简介")
        if "写一段不剧透" in publish_text:
            errors.append("publish.md 仍是初始模板")
        hashtags = re.findall(r"(?<!\w)#[\w\u4e00-\u9fff]+", publish_text)
        if not hashtags:
            errors.append("publish.md 至少需要一个 #话题")
        if len(hashtags) > 5:
            errors.append(f"publish.md 有 {len(hashtags)} 个 #话题，最多只能有 5 个")
    errors.extend(inspect_wav(project / "audio/narration.wav", "旁白总轨"))
    if require_video:
        errors.extend(inspect_wav(project / "audio/score.wav", "背景音乐与事件音轨"))
        narration_seconds = wav_duration(project / "audio/narration.wav")
        score_seconds = wav_duration(project / "audio/score.wav")
        if narration_seconds and score_seconds < narration_seconds - 0.5:
            errors.append(
                f"背景音乐没有覆盖全片：背景 {score_seconds:.1f}s，旁白时间轴 {narration_seconds:.1f}s"
            )
        errors.extend(inspect_video_audio(project / "renders/final.mp4"))
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="商业发布前许可和文件检查")
    parser.add_argument("project", type=Path)
    parser.add_argument("--no-video", action="store_true")
    args = parser.parse_args()
    errors = inspect(Path(os.path.abspath(args.project)), require_video=not args.no_video)
    if errors:
        print("预检失败：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(2)
    print("预检通过")


if __name__ == "__main__":
    main()
