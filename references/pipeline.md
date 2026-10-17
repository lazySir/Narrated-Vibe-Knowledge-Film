# 工程格式与命令

## 项目结构

```text
projects/001_标题/
├── project.json
├── license-manifest.json
├── facts.md
├── script.md
├── publish.md
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

`publish.md` 保存可直接发布的中文简介，正文之后附一到五个相关 `#话题`。
发布预检会拒绝缺少简介、仍是模板、没有话题或超过五个话题的工程。

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

每个工程还必须独立创作 `cover.jpg`：固定为 1440×2560 的 9:16 高清竖图，禁止从成片
截图。封面应以手机端小图可读为准，只保留一个清楚的冲突，使用醒目的简体中文大字，
并检查所有文字和数字。导出高质量 JPEG，避免重度压缩或放大低清截图。生成来源及商用
状态写入 `license-manifest.json`。

归档会同时生成 `NNN_标题.mp4`、`NNN_标题_封面.jpg` 和
`NNN_标题_简介.txt`。

`engine/audio.py --wav-only` 根据事件表生成覆盖全片的 `audio/score.wav`。它是必需的，
所以默认不会生成只有人声、没有音乐的成片。混音脚本会先稳定旁白响度，再把合成底乐
保持在 0 dB；若提供外部 `--bgm`，默认降到 -14 dB。所有背景层在人声出现时都会
自动平滑降低，停顿时缓慢回升。普通使用直接运行命令即可，不需要自己理解或填写音频参数。

外部 BGM 应选择无歌词、节奏稀疏、没有密集鼓点和尖锐高频的器乐。脚本会拒绝高于
-8 dB 的外部 BGM 和高于 0 dB 的合成底乐设置。最终文件才会进入 `成品/`。

在 `film.js` 的 `meta` 中设置 `music_preset`：`night-tech`、
`social-tension`、`math-clarity` 或 `fable-warm`。未设置时使用
`night-tech`。预设改变调式、和弦、低频床和稀疏节拍，但都保持全片连续并接受人声避让。
