$ErrorActionPreference = 'Stop'
$env:NO_PROXY = '*'
$env:HTTP_PROXY = ''
$env:HTTPS_PROXY = ''
$env:ALL_PROXY = ''
$root = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $root '.runtime'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $runtime 'python'
$env:HF_HOME = Join-Path $runtime 'huggingface'
$env:HF_HUB_CACHE = Join-Path $env:HF_HOME 'hub'
$repo = Join-Path $runtime 'CosyVoice'
$venv = Join-Path $root '.venv-cosyvoice3'
$model = Join-Path $root 'models\Fun-CosyVoice3-0.5B-2512'

function Find-BasePython {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw '找不到可用于安装 uv 的 Python。'
}

New-Item -ItemType Directory -Force $runtime, (Join-Path $root 'models') | Out-Null
$basePython = Find-BasePython

& $basePython -m pip install --index-url https://pypi.org/simple --upgrade uv
if ($LASTEXITCODE -ne 0) { throw '安装 uv 失败。' }
$uv = Join-Path (Split-Path -Parent $basePython) 'Scripts\uv.exe'
if (-not (Test-Path $uv)) { $uv = (Get-Command uv -ErrorAction Stop).Source }

if (-not (Test-Path $repo)) {
    git clone --recursive --depth 1 https://github.com/QwenAudio/CosyVoice.git $repo
    if ($LASTEXITCODE -ne 0) { throw '下载 CosyVoice 源码失败。' }
}

$python = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $python)) {
    & $uv venv $venv --python 3.10
    if ($LASTEXITCODE -ne 0) { throw '创建 Python 3.10 环境失败。' }
}

& $uv pip install --python $python 'setuptools<81' wheel
if ($LASTEXITCODE -ne 0) { throw '安装 Python 构建组件失败。' }
& $uv pip install --python $python --no-build-isolation 'openai-whisper==20231117'
if ($LASTEXITCODE -ne 0) { throw '安装 Whisper 依赖失败。' }
& $uv pip install --python $python --index-strategy unsafe-best-match -r (Join-Path $repo 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw '安装 CosyVoice3 依赖失败。' }

if (-not (Test-Path $model)) {
    $script = @'
from huggingface_hub import snapshot_download
import sys
snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', local_dir=sys.argv[1])
'@
    $script | & $python - $model
    if ($LASTEXITCODE -ne 0) { throw '下载 CosyVoice3 模型失败。' }
}

Write-Host 'CosyVoice3 已安装。首次使用时请建立 voices/narrator.json 和一次性参考录音，以后所有影片复用。'
Write-Host '生成命令：.venv-cosyvoice3/Scripts/python.exe scripts/tts_generate.py <项目> --provider cosyvoice3'
