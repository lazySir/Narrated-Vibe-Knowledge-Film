$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env:NO_PROXY = '*'
$env:HTTP_PROXY = ''
$env:HTTPS_PROXY = ''
$env:ALL_PROXY = ''
$python = "$root\.venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw '请先运行 scripts/setup.ps1。' }
& $python -m venv "$root\.venv-chattts"
$chatPython = "$root\.venv-chattts\Scripts\python.exe"
& $chatPython -m pip install --index-url https://pypi.org/simple --upgrade pip
if ($LASTEXITCODE -ne 0) { throw '升级 ChatTTS 环境的 pip 失败。' }
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    & $chatPython -m pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.4.1 torchaudio==2.4.1
    if ($LASTEXITCODE -ne 0) { throw '安装 CUDA 版 PyTorch 失败。' }
} else {
    & $chatPython -m pip install --index-url https://pypi.org/simple torch==2.4.1 torchaudio==2.4.1
    if ($LASTEXITCODE -ne 0) { throw '安装 CPU 版 PyTorch 失败。' }
}
& $chatPython -m pip install --index-url https://pypi.org/simple -r "$root\requirements-chattts.txt"
if ($LASTEXITCODE -ne 0) { throw '安装 ChatTTS 依赖失败。' }
Write-Host 'ChatTTS 试音环境已完成。官方模型为 CC BY-NC 4.0，禁止用于商业成片。'
