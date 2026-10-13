$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env:NO_PROXY = '*'
$env:HTTP_PROXY = ''
$env:HTTPS_PROXY = ''
$env:ALL_PROXY = ''

function Find-Python {
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidate = Get-ChildItem "$env:USERPROFILE\.cache\codex-runtimes" -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'dependencies\\python\\python.exe$' } |
        Select-Object -First 1
    if ($candidate) { return $candidate.FullName }
    throw '找不到 Python 3.11 或 3.12。请先安装 Python。'
}

$python = Find-Python
& $python -m venv "$root\.venv"
$venvPython = "$root\.venv\Scripts\python.exe"
& $venvPython -m pip install --index-url https://pypi.org/simple --upgrade pip
if ($LASTEXITCODE -ne 0) { throw '升级 pip 失败。' }
& $venvPython -m pip install --index-url https://pypi.org/simple -r "$root\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw '安装 Python 依赖失败。' }
& $venvPython -m playwright install chromium
if ($LASTEXITCODE -ne 0) { throw '安装 Playwright Chromium 失败。' }
New-Item -ItemType Directory -Force "$root\成品", "$root\projects" | Out-Null
Write-Host '基础环境已完成。运行 scripts/check_environment.py 检查 FFmpeg。'
