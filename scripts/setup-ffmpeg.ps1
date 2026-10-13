$ErrorActionPreference = 'Stop'
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    ffmpeg -version | Select-Object -First 1
    exit 0
}
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw '找不到 winget。请从 ffmpeg.org 的 Windows builds 安装 FFmpeg 并加入 PATH。'
}
winget install --id Gyan.FFmpeg --exact --accept-package-agreements --accept-source-agreements
Write-Host 'FFmpeg 已安装。请重新打开终端后运行 scripts/check_environment.py。'
