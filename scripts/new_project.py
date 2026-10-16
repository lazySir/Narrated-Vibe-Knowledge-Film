#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(os.path.abspath(__file__)).parent.parent


def clean_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value or "未命名"


def next_number(base: Path) -> int:
    found = []
    if base.exists():
        for item in base.iterdir():
            match = re.match(r"^(\d{3})_", item.name)
            if match:
                found.append(int(match.group(1)))
    return max(found, default=0) + 1


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="创建一条带旁白知识片工程")
    parser.add_argument("title")
    parser.add_argument("--world", choices=["B", "C", "b", "c"], default="C")
    parser.add_argument("--usage", choices=["commercial", "non-commercial"], default="commercial")
    parser.add_argument("--projects-dir", type=Path, default=ROOT / "projects")
    args = parser.parse_args()

    base = Path(os.path.abspath(args.projects_dir))
    base.mkdir(parents=True, exist_ok=True)
    number = next_number(base)
    title = clean_name(args.title)
    project = base / f"{number:03d}_{title}"
    if project.exists():
        raise SystemExit(f"工程已经存在：{project}")

    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/new_film.py"), str(project), "--world", args.world.upper()],
            check=True,
        )
    except Exception:
        if project.exists():
            shutil.rmtree(project)
        raise
    (project / "audio/voice").mkdir(parents=True, exist_ok=True)
    (project / "renders").mkdir(exist_ok=True)
    (project / "generated_subs.js").write_text("window.GENERATED_SUBS = [];\n", encoding="utf-8")
    voice_profile_path = ROOT / "voices/narrator.json"
    voice_profile = {}
    if voice_profile_path.exists():
        voice_profile = json.loads(voice_profile_path.read_text(encoding="utf-8"))
    voice_rights_ready = voice_profile.get("rights_confirmed") is True

    dump(project / "project.json", {
        "sequence": number,
        "title": args.title,
        "world": args.world.upper(),
        "usage": args.usage,
        "created_on": date.today().isoformat(),
    })
    dump(project / "narration.json", {"lines": []})
    dump(project / "pronunciation.json", {})
    dump(project / "voice.json", {
        "provider": "cosyvoice3",
        "model": "FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
        "model_dir": "models/Fun-CosyVoice3-0.5B-2512",
        "voice_profile": "voices/narrator.json",
        "voice": "project-owned-reference",
        "device": "cpu",
        "fp16": False,
        "speed": 1.0,
        "instruction": "请用平静、清楚、有探索感的普通话讲述，自然停顿，避免广告腔和夸张播音腔。",
    })
    dump(project / "license-manifest.json", {
        "usage": args.usage,
        "assets": [{
            "kind": "tts",
            "name": "CosyVoice3 0.5B + 项目自有参考声音",
            "source": "https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512",
            "license": "Apache-2.0；" + str(voice_profile.get("rights_note", "参考声音必须由项目方拥有或取得商业授权")),
            "checked_on": date.today().isoformat() if voice_rights_ready else "",
            "status": "approved" if voice_rights_ready else "unverified",
        }],
    })
    (project / "facts.md").write_text("# 事实表\n\n| 事实 | 来源 | 把握 | 用在何处 |\n|---|---|---|---|\n", encoding="utf-8")
    (project / "script.md").write_text(f"# 《{args.title}》旁白稿\n\n", encoding="utf-8")
    (project / "publish.md").write_text(
        "# 发布简介\n\n"
        "写一段不剧透核心结论、能让观众理解问题并愿意评论的简介。\n\n"
        "#知识科普\n",
        encoding="utf-8",
    )
    (project / "storyboard.md").write_text(
        "# 分镜表\n\n| ID | 旁白 | 屏上主体 | 动作 | 景别 | 关键词时刻 | 观众理解 | 声音 | 来源 |\n"
        "|---|---|---|---|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    print(project)


if __name__ == "__main__":
    main()
