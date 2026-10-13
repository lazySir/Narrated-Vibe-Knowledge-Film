#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path

ALLOWED = {"approved", "original", "public-domain"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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
    if require_video and not (project / "renders/final.mp4").exists():
        errors.append("缺少 renders/final.mp4")
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
