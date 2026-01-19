#!/usr/bin/env pwsh
# Script para criar release automaticamente no GitHub
# Uso: .\create-release.ps1 token [version]

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Token,
    
    [Parameter(Mandatory=$false, Position=1)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoOwner = "lopesleo",
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "Discord-Lite"
)

$ErrorActionPreference = "Stop"

# Detectar versão do plugin.json se não for informada
if ([string]::IsNullOrEmpty($Version)) {
    if (Test-Path "$PSScriptRoot/plugin.json") {
        try {
            $pluginJson = Get-Content "$PSScriptRoot/plugin.json" -Raw | ConvertFrom-Json
            $Version = "v" + $pluginJson.version
        } catch {
            Write-Warning "Failed to read version from plugin.json"
            $Version = "v1.0.0"
        }
    } else {
        $Version = "v1.0.0"
    }
}

Write-Host "Creating GitHub Release for $Version..." -ForegroundColor Cyan

# Configurações
$apiUrl = "https://api.github.com"
$headers = @{
    "Authorization" = "Bearer $Token"
    "Accept" = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}

# Nome do arquivo zip
$zipFile = "Discord-Lite-$Version.zip"
$zipPath = Join-Path $PSScriptRoot $zipFile

# Verificar se o zip existe
if (-not (Test-Path $zipPath)) {
    Write-Host "File $zipFile not found!" -ForegroundColor Red
    Write-Host "Creating zip file..." -ForegroundColor Yellow
    
    # Criar temp folder
    $tempDir = Join-Path $PSScriptRoot "temp_release"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    # Copiar arquivos essenciais
    $files = @('main.py', 'plugin.json', 'package.json', 'README.md', 'LICENSE')
    foreach ($file in $files) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $tempDir
        }
    }
    
    # Copiar pastas (excluindo __pycache__)
    $folders = @('dist', 'defaults', 'lib', 'assets')
    foreach ($folder in $folders) {
        if (Test-Path $folder) {
            Copy-Item $folder -Destination $tempDir -Recurse -Force
        }
    }
    
    # Remover __pycache__ e outros arquivos indesejados
    Get-ChildItem -Path $tempDir -Recurse -Force | Where-Object { 
        $_.Name -eq '__pycache__' -or 
        $_.Name -eq '.pyc' -or 
        $_.Name -eq '.DS_Store' -or
        $_.Name -eq 'Thumbs.db'
    } | Remove-Item -Recurse -Force
    
    # Criar zip
    Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -Force
    
    # Limpar temp
    Remove-Item $tempDir -Recurse -Force
    
    Write-Host "Zip file created!" -ForegroundColor Green
}

# Corpo do release
$releaseBody = @"
## Discord Lite $Version

### What's New in v1.1.0
- **Game Activity Sync**: Automatically displays the Steam game you are currently playing as your Discord status! No more "Deckord" - it now shows the real game name with Rich Presence art.
- **Performance Improvements**: Optimized background polling to reduce CPU usage and save battery.
- **Improved Caching**: App IDs are now cached persistently, making game detection faster and reducing network requests.
- **Fixes**:
    - Fixed SSL certificate errors on Steam Deck native python environment.
    - Fixed redundant text in status display (e.g. "Cuphead Cuphead").

### Features
- Full voice chat controls (mute, deafen, join/leave)
- Per-user volume control with memory
- Server and channel browsing
- Member list with speaking indicators
- Call timer
- Toast notifications for voice events
- Auto-connect option
- Multi-language support (EN/PT)
- Professional Discord-themed UI

### Requirements
- Steam Deck with [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
- Discord desktop app (Flatpak recommended)

### Installation
1. Download ``Discord-Lite-$Version.zip``
2. Extract to ``~/homebrew/plugins/``
3. Restart Decky Loader

### Usage
See [README.md](https://github.com/$RepoOwner/$RepoName#readme) for detailed instructions.
"@

# Criar o release
Write-Host "Creating release $Version..." -ForegroundColor Yellow

$releaseData = @{
    tag_name = $Version
    target_commitish = "main"
    name = "Discord Lite $Version - Full Voice Chat Integration"
    body = $releaseBody
    draft = $false
    prerelease = $false
} | ConvertTo-Json

try {
    $release = Invoke-RestMethod -Uri "$apiUrl/repos/$RepoOwner/$RepoName/releases" `
        -Method Post `
        -Headers $headers `
        -Body $releaseData `
        -ContentType "application/json"
    
    Write-Host "Release created successfully!" -ForegroundColor Green
    Write-Host "URL: $($release.html_url)" -ForegroundColor Cyan
    
    # Upload do arquivo zip
    Write-Host "Uploading $zipFile..." -ForegroundColor Yellow
    
    $uploadUrl = $release.upload_url -replace '\{\?name,label\}', "?name=$zipFile"
    
    $zipBytes = [System.IO.File]::ReadAllBytes($zipPath)
    
    $uploadHeaders = @{
        "Authorization" = "Bearer $Token"
        "Accept" = "application/vnd.github+json"
        "Content-Type" = "application/zip"
    }
    
    $asset = Invoke-RestMethod -Uri $uploadUrl `
        -Method Post `
        -Headers $uploadHeaders `
        -Body $zipBytes
    
    Write-Host "File uploaded successfully!" -ForegroundColor Green
    Write-Host "Download: $($asset.browser_download_url)" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "Release $Version published successfully!" -ForegroundColor Green
    Write-Host "$($release.html_url)" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error creating release:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "Detalhes: $($errorJson.message)" -ForegroundColor Red
    }
    
    exit 1
}
