# Narrated Vibe Knowledge Film

一个面向中文知识短视频的 Codex Skill。它在
[`vibe-knowledge-film`](https://github.com/Dave-cc/vibe-knowledge-film)
的 Canvas 动画引擎上加入旁白、统一时间轴、字幕同步、商业许可门禁和成品编号。

支持两种视觉世界：

- **C 夜曲**：抽象概念、科学机制、数学和哲学。
- **B 寓言**：心理、行为、动物实验和生活场景。

## 最重要的许可规则

你可以把本仓库生成的视频用于抖音变现，但每个外部素材和语音模型必须另行允许商业使用。

默认旁白使用本地 `Fun-CosyVoice3-0.5B-2512`。官方代码和模型权重均标为 Apache 2.0，可用于商业工作流；参考声音仍必须由你本人录制，或另行取得商业授权。项目会在没有确认参考声音权利时阻止发布。

完整说明见 [商业发布清单](references/commercial-release.md) 和
[第三方声明](THIRD_PARTY_NOTICES.md)。

## 目录

```text
SKILL.md               Skill 入口
engine/                Canvas、逐帧渲染、事件音效
scripts/               建工程、配音、时间轴、混音和成品编号
references/            工作流、格式和许可说明
projects/              每条片的工作工程（默认忽略）
成品/                  最终视频（Git 忽略）
```

成品文件自动命名为：

```text
001_标题.mp4
002_下一个标题.mp4
```

编号从 `成品/` 中现有文件的最大序号继续递增。

## 安装

在 PowerShell 中运行：

```powershell
./scripts/setup.ps1
```

它会建立项目虚拟环境并安装动画引擎依赖。安装 CosyVoice3 本地配音环境：

```powershell
./scripts/setup-cosyvoice3.ps1
```

CosyVoice3 模型首次使用时需要下载。GTX 1650 Ti 4GB 属于 FP16 推理下限，流程默认逐句生成；若显存不足，把项目 `voice.json` 的 `device` 改成 `cpu`。

机器还需要 Google Chrome 和 FFmpeg。运行环境检查：

```powershell
./.venv/Scripts/python.exe scripts/check_environment.py
```

## 快速开始

创建项目：

```powershell
./.venv/Scripts/python.exe scripts/new_project.py "标题" --world C --usage commercial
```

在项目的 `narration.json` 中填写旁白句子。第一次使用时，把
`references/narrator.example.json` 复制为 `voices/narrator.json`，把一段干净、
单人、普通话参考录音放进 `voices/narrator-reference.wav`，填写完全一致的逐字稿，
并在确认拥有商业使用权后设置 `rights_confirmed: true`。这份固定音色档案会被以后
所有影片复用，无需每部重新录音；`voices/` 默认不会提交到 GitHub。

生成旁白并创建时间轴：

```powershell
./.venv-cosyvoice3/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider cosyvoice3
./.venv/Scripts/python.exe scripts/build_timeline.py projects/001_标题
```

完成画面后渲染、混音并归档：

```powershell
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --jobs 4
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --events
./.venv/Scripts/python.exe engine/audio.py projects/001_标题 --wav-only
./.venv/Scripts/python.exe scripts/mix_narration.py projects/001_标题
./.venv/Scripts/python.exe scripts/archive_final.py projects/001_标题 --title "标题"
```

也可以使用经过商业授权的 OpenAI 兼容语音接口：

```powershell
./.venv/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider openai-compatible
```

## 发布到 GitHub

仓库只提交 Skill、引擎、脚本和文档。`projects/`、`成品/`、模型、虚拟环境、密钥和生成音频均已忽略。发布前运行：

```powershell
./.venv/Scripts/python.exe scripts/preflight_release.py projects/001_标题
```

本项目不包含上游参考片、样片 GIF、拆片字幕或不获许可的画面设计。
