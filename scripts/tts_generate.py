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


class CosyVoice3Backend:
    def __init__(self, project: Path, voice_cfg: dict):
        root = Path(os.path.abspath(__file__)).parent.parent
        effective_cfg = dict(voice_cfg)
        profile_path = None
        if voice_cfg.get("voice_profile"):
            profile_path = Path(str(voice_cfg["voice_profile"]))
            if not profile_path.is_absolute():
                profile_path = root / profile_path
            if not profile_path.exists():
                raise SystemExit(
                    f"找不到固定旁白音色档案：{profile_path}。请复制 references/narrator.example.json "
                    "到 voices/narrator.json，并放入一次性参考录音。"
                )
            profile_cfg = load_json(profile_path)
            effective_cfg = {**profile_cfg, **voice_cfg}
        repo = root / ".runtime/CosyVoice"
        model_dir = Path(effective_cfg.get("model_dir") or root / "models/Fun-CosyVoice3-0.5B-2512")
        if not model_dir.is_absolute():
            model_dir = root / model_dir
        prompt_wav = Path(effective_cfg.get("prompt_wav", ""))
        if not prompt_wav.is_absolute():
            prompt_wav = (profile_path.parent if profile_path else project) / prompt_wav
        prompt_text = str(effective_cfg.get("prompt_text", "")).strip()
        instruction = str(effective_cfg.get("instruction", "")).strip()
        if not repo.exists() or not model_dir.exists():
            raise SystemExit("CosyVoice3 尚未安装。请先运行 scripts/setup-cosyvoice3.ps1。")
        if not prompt_wav.exists():
            raise SystemExit("CosyVoice3 找不到参考录音 prompt_wav。请使用你拥有声音权利的参考录音。")
        if not instruction and not prompt_text:
            raise SystemExit("CosyVoice3 零样本模式需要与参考录音逐字对应的 prompt_text。")
        if effective_cfg.get("rights_confirmed") is not True:
            raise SystemExit("固定音色档案的 rights_confirmed 不是 true；无法确认参考声音可用于商业项目。")
        device = str(effective_cfg.get("device", "gpu")).lower()
        if device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        sys.path.insert(0, str(repo))
        sys.path.insert(0, str(repo / "third_party/Matcha-TTS"))
        try:
            import torch
            from cosyvoice.cli.cosyvoice import AutoModel
        except ImportError as exc:
            raise SystemExit("当前环境没有 CosyVoice3。请用 .venv-cosyvoice3 运行本脚本。") from exc
        self.torch = torch
        self.model = AutoModel(
            model_dir=str(model_dir),
            fp16=bool(effective_cfg.get("fp16", True) and device != "cpu"),
        )
        self.prompt_wav = str(prompt_wav)
        self.prompt_text = "You are a helpful assistant.<|endofprompt|>" + prompt_text
        self.voice_cfg = effective_cfg
        self.profile_path = str(profile_path) if profile_path else ""
        self.rights_confirmed = effective_cfg.get("rights_confirmed") is True

    def generate(self, text: str, output: Path) -> None:
        import soundfile as sf
        instruction = str(self.voice_cfg.get("instruction", "")).strip()
        speed = float(self.voice_cfg.get("speed", 1.0))
        if instruction:
            control = "You are a helpful assistant. " + instruction + "<|endofprompt|>"
            stream = self.model.inference_instruct2(
                text, control, self.prompt_wav, stream=False, speed=speed
            )
        else:
            stream = self.model.inference_zero_shot(
                text, self.prompt_text, self.prompt_wav, stream=False, speed=speed
            )
        chunks = [item["tts_speech"].detach().cpu() for item in stream]
        if not chunks:
            raise RuntimeError("CosyVoice3 没有返回音频。")
        wav = self.torch.cat(chunks, dim=1).squeeze(0).numpy()
        sf.write(output, wav, self.model.sample_rate, subtype="PCM_16")


def main() -> None:
    parser = argparse.ArgumentParser(description="逐句生成旁白")
    parser.add_argument("project", type=Path)
    parser.add_argument("--provider", choices=["openai-compatible", "cosyvoice3"])
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = Path(os.path.abspath(args.project))
    root = Path(os.path.abspath(__file__)).parent.parent
    os.environ.setdefault("HF_HOME", str(root / ".cache/huggingface"))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(root / ".cache/huggingface/transformers"))
    os.environ.setdefault("TORCH_HOME", str(root / ".cache/torch"))
    os.environ.setdefault("MPLCONFIGDIR", str(root / ".cache/matplotlib"))
    for cache_dir in ("HF_HOME", "TRANSFORMERS_CACHE", "TORCH_HOME", "MPLCONFIGDIR"):
        Path(os.environ[cache_dir]).mkdir(parents=True, exist_ok=True)
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
    backend = CosyVoice3Backend(project, voice_cfg) if provider == "cosyvoice3" else None

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
        if provider == "cosyvoice3":
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
        "voice_profile": backend.profile_path if provider == "cosyvoice3" else "",
        "prompt_wav": backend.prompt_wav if provider == "cosyvoice3" else "",
        "rights_confirmed": backend.rights_confirmed if provider == "cosyvoice3" else None,
        "generated": generated,
    }
    (project / "audio/generation.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
