# Narrated Vibe Knowledge Film

一个面向中文知识短视频的 Codex Skill。它在
[`vibe-knowledge-film`](https://github.com/Dave-cc/vibe-knowledge-film)
的 Canvas 动画引擎上加入旁白、统一时间轴、字幕同步、商业许可门禁和成品编号。

支持两种视觉世界：

- **C 夜曲**：抽象概念、科学机制、数学和哲学。
- **B 寓言**：心理、行为、动物实验和生活场景。

## 最重要的许可规则

你可以把本仓库生成的视频用于抖音变现，但每个外部素材和语音模型必须另行允许商业使用。

ChatTTS 官方模型采用 CC BY-NC 4.0，只能用于本地试音或非商业样片。正式发布时请配置一个明确允许商业使用的 TTS 服务。本项目在 `usage: commercial` 时会拒绝调用 ChatTTS，防止误发布。

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

它会建立项目虚拟环境并安装动画引擎依赖。安装 ChatTTS 试音环境：

```powershell
./scripts/setup-chattts.ps1
```

ChatTTS 模型首次使用时需要下载，至少约 4GB 显存；本机 4GB 显存属于最低边缘配置，脚本默认关闭编译并逐句生成。

机器还需要 Google Chrome 和 FFmpeg。运行环境检查：

```powershell
./.venv/Scripts/python.exe scripts/check_environment.py
```

## 快速开始

创建项目：

```powershell
./.venv/Scripts/python.exe scripts/new_project.py "标题" --world C --usage commercial
```

在项目的 `narration.json` 中填写旁白句子。商业 TTS 使用 `.env` 中的 OpenAI 兼容接口；供应商和声音的商业授权由你确认，并记录到项目的 `license-manifest.json`。

生成旁白并创建时间轴：

```powershell
./.venv/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider openai-compatible
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

使用 ChatTTS 做非商业试音：

```powershell
./.venv-chattts/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider chattts --preview-only
```

## 发布到 GitHub

仓库只提交 Skill、引擎、脚本和文档。`projects/`、`成品/`、模型、虚拟环境、密钥和生成音频均已忽略。发布前运行：

```powershell
./.venv/Scripts/python.exe scripts/preflight_release.py projects/001_标题
```

本项目不包含上游参考片、样片 GIF、拆片字幕或不获许可的画面设计。
