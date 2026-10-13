# 工程格式与命令

## 项目结构

```text
projects/001_标题/
├── project.json
├── license-manifest.json
├── facts.md
├── script.md
├── storyboard.md
├── narration.json
├── pronunciation.json
├── voice.json
├── timeline.json
├── subtitles.srt
├── generated_subs.js
├── index.html
├── film.js
├── audio/
│   ├── voice/
│   ├── narration.wav
│   ├── events.json
│   └── score.wav
└── renders/
    ├── preview-30s.mp4
    ├── raw.mp4
    └── final.mp4
```

`narration.json`：

```json
{
  "lines": [
    {"id": "001", "text": "骰子停下以前，没有人知道答案。"},
    {"id": "002", "text": "可如果掷两万五千次，比例会慢慢稳定。"}
  ]
}
```

`voice.json` 保存提供商配置，不保存密钥：

```json
{
  "provider": "openai-compatible",
  "model": "gpt-4o-mini-tts",
  "voice": "已获商业授权的 voice id",
  "response_format": "wav",
  "instructions": "平静、清楚、有探索感，避免广告腔"
}
```

`license-manifest.json`：

```json
{
  "usage": "commercial",
  "assets": [
    {
      "kind": "tts",
      "name": "供应商 / 模型 / voice",
      "source": "https://正式条款网址",
      "license": "当前商业计划允许生成内容用于变现短视频",
      "checked_on": "YYYY-MM-DD",
      "status": "approved"
    }
  ]
}
```

## 建工程

```powershell
./.venv/Scripts/python.exe scripts/new_project.py "标题" --world C --usage commercial
```

世界只能为 `B` 或 `C`。标题会清理 Windows 文件名中的非法字符。

## 生成旁白

商业后端：

```powershell
./.venv/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider openai-compatible
```

所需环境变量：`TTS_BASE_URL`、`TTS_API_KEY`、`TTS_MODEL`、`TTS_VOICE`。
项目的 `voice.json` 会覆盖模型、voice 和 instructions，但密钥只从环境变量读取。

本地 CosyVoice3：

```powershell
./.venv-cosyvoice3/Scripts/python.exe scripts/tts_generate.py projects/001_标题 --provider cosyvoice3
```

脚本逐句写入 `audio/voice/NNN.wav`。已有且非空的文件默认跳过，使用
`--force` 才覆盖。固定参考声音放在仓库根目录 `voices/` 中，
`voices/narrator.json` 必须设置 `rights_confirmed: true`。默认 instruct2 模式不读取
逐字稿；改用零样本模式时，`prompt_text` 必须与录音逐字一致。所有影片默认复用
这一个音色档案。本机 GTX 1650 Ti 4GB 默认使用 CPU/FP32；FP16 输出会进行
非有限数值和全静音检查，检测到坏音频时立即停止。

## 时间轴

```powershell
./.venv/Scripts/python.exe scripts/build_timeline.py projects/001_标题
```

默认每句前留 0.12 秒、句后留 0.30 秒，并以实际 WAV 长度为准。
输出 `timeline.json`、`subtitles.srt` 和可被 `index.html` 加载的
`generated_subs.js`。

## 画面、声音与归档

```powershell
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --sheet 16
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --clip 0 30 preview-30s
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --jobs 4
./.venv/Scripts/python.exe engine/render.py projects/001_标题 --events
./.venv/Scripts/python.exe engine/audio.py projects/001_标题 --wav-only
./.venv/Scripts/python.exe scripts/mix_narration.py projects/001_标题
./.venv/Scripts/python.exe scripts/preflight_release.py projects/001_标题
./.venv/Scripts/python.exe scripts/archive_final.py projects/001_标题 --title "标题"
```

`engine/audio.py --wav-only` 根据事件表生成 `audio/score.wav`。混音脚本以旁白为中心：事件音乐轨在有人声时降低，并输出 48kHz AAC。
若提供 `--bgm`，背景音乐同样自动闪避。最终文件才会进入 `成品/`。
