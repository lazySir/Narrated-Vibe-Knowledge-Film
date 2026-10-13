#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

from preflight_release import inspect

ROOT = Path(os.path.abspath(__file__)).parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def clean_name(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    return value or "未命名"


def main() -> None:
    parser = argparse.ArgumentParser(description="把终检通过的视频复制到成品目录并自动编号")
    parser.add_argument("project", type=Path)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()
    project = Path(os.path.abspath(args.project))
    errors = inspect(project, require_video=True)
    if errors:
        print("不能归档：")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(2)

    destination = ROOT / "成品"
    destination.mkdir(exist_ok=True)
    numbers = []
    for item in destination.glob("*.mp4"):
        match = re.match(r"^(\d{3})_", item.name)
        if match:
            numbers.append(int(match.group(1)))
    number = max(numbers, default=0) + 1
    output = destination / f"{number:03d}_{clean_name(args.title)}.mp4"
    shutil.copy2(project / "renders/final.mp4", output)
    print(output)


if __name__ == "__main__":
    main()
