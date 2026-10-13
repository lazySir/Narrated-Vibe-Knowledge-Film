#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from runtime import ffmpeg

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def normalized(text: str, pronunciation: dict) -> str:
    for source in sorted(pronunciation, key=len, reverse=True):
        text = text.replace(source, str(pronunciation[source]))
    return text.strip()


def commercial_guard(project: Path, provider: str, preview_only: bool) -> str:
    manifest = load_json(project / "license-manifest.json")
    usage = manifest.get("usage", "commercial")
    if provider == "chattts" and (usage == "commercial" or not preview_only):
        raise SystemExit(
            "拒绝生成：ChatTTS 官方模型是 CC BY-NC 4.0。商业工程只能把它用于明确标记的本地试音。"
            "如需试音，请把项目 usage 改为 non-commercial 并加 --preview-only；正式成片请使用有商业授权的后端。"
        )
    return usage


def openai_compatible(text: str, output: Path, voice_cfg: dict) -> None:
    base = os.getenv("TTS_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.getenv("TTS_API_KEY", "")
    model = voice_cfg.get("model") or os.getenv("TTS_MODEL", "")
    voice = voice_cfg.get("voice") or os.getenv("TTS_VOICE", "")
    response_format = voice_cfg.get("response_format", "wav")
    if not key or not model or not voice:
        raise SystemExit("缺少 TTS_API_KEY、TTS_MODEL 或 TTS_VOICE。请复制 .env.example 为 .env 后填写。")
    body = {"model": model, "voice": voice, "input": text, "response_format": response_format}
    if voice_cfg.get("instructions"):
        body["instructions"] = voice_cfg["instructions"]
    request = urllib.request.Request(
        f"{base}/audio/speech",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise SystemExit(f"TTS 请求失败：HTTP {exc.code} {detail}") from exc
    if response_format == "wav":
        output.write_bytes(data)
        return
    temp = output.with_suffix(f".{response_format}")
    temp.write_bytes(data)
    subprocess.run([ffmpeg(), "-v", "error", "-y", "-i", str(temp), str(output)], check=True)
    temp.unlink()


class ChatTTSBackend:
    def __init__(self, project: Path, voice_cfg: dict):
        try:
            import ChatTTS
        except ImportError as exc:
            raise SystemExit("当前环境没有 ChatTTS。请先运行 scripts/setup-chattts.ps1。") from exc
        self.ChatTTS = ChatTTS
        self.chat = ChatTTS.Chat()
        loaded = self.chat.load(source="huggingface", compile=False)
        if not loaded:
            raise SystemExit("ChatTTS 模型下载或加载失败。请检查网络和 .cache/huggingface 的可写权限。")
        self.speaker_path = project / "audio/chattts-speaker.txt"
        if self.speaker_path.exists():
            self.speaker = self.speaker_path.read_text(encoding="utf-8").strip()
        else:
            self.speaker = self.chat.sample_random_speaker()
            if not isinstance(self.speaker, str):
                raise SystemExit("当前 ChatTTS 版本未返回可持久化的 speaker 字符串，请固定兼容版本后重试。")
            self.speaker_path.write_text(self.speaker, encoding="utf-8")
        self.voice_cfg = voice_cfg

    def generate(self, text: str, output: Path) -> None:
        import soundfile as sf
        params_code = self.ChatTTS.Chat.InferCodeParams(
            spk_emb=self.speaker,
            temperature=float(self.voice_cfg.get("temperature", 0.3)),
            top_P=float(self.voice_cfg.get("top_P", 0.7)),
            top_K=int(self.voice_cfg.get("top_K", 20)),
        )
        params_text = self.ChatTTS.Chat.RefineTextParams(
            prompt=self.voice_cfg.get("chattts_prompt", "[oral_1][laugh_0][break_4]")
        )
        wavs = self.chat.infer([text], params_refine_text=params_text, params_infer_code=params_code)
        sf.write(output, wavs[0], 24000, subtype="PCM_16")


def main() -> None:
    parser = argparse.ArgumentParser(description="逐句生成旁白")
    parser.add_argument("project", type=Path)
    parser.add_argument("--provider", choices=["openai-compatible", "chattts"])
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = Path(os.path.abspath(args.project))
    root = Path(os.path.abspath(__file__)).parent.parent
    os.environ.setdefault("HF_HOME", str(root / ".cache/huggingface"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(root / ".cache/huggingface/transformers"))
    os.environ.setdefault("TORCH_HOME", str(root / ".cache/torch"))
    load_dotenv(root / ".env")
    voice_cfg = load_json(project / "voice.json")
    provider = args.provider or voice_cfg.get("provider", "openai-compatible")
    usage = commercial_guard(project, provider, args.preview_only)
    lines = load_json(project / "narration.json").get("lines", [])
    pronunciation = load_json(project / "pronunciation.json")
    if not lines:
        raise SystemExit("narration.json 里没有旁白句子。")
    out_dir = project / "audio/voice"
    out_dir.mkdir(parents=True, exist_ok=True)
    backend = ChatTTSBackend(project, voice_cfg) if provider == "chattts" else None

    generated = []
    for index, item in enumerate(lines, 1):
        line_id = str(item.get("id") or f"{index:03d}")
        text = normalized(str(item.get("text", "")), pronunciation)
        if not text:
            raise SystemExit(f"第 {index} 句为空。")
        output = out_dir / f"{line_id}.wav"
        if output.exists() and output.stat().st_size > 44 and not args.force:
            print(f"skip {output.name}")
            continue
        print(f"generate {output.name}: {text}", flush=True)
        if provider == "chattts":
            backend.generate(text, output)
        else:
            openai_compatible(text, output, voice_cfg)
        generated.append(output.name)

    record = {
        "provider": provider,
        "usage": usage,
        "preview_only": bool(args.preview_only),
        "model": voice_cfg.get("model") or os.getenv("TTS_MODEL", ""),
        "voice": voice_cfg.get("voice") or os.getenv("TTS_VOICE", ""),
        "generated": generated,
    }
    (project / "audio/generation.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
