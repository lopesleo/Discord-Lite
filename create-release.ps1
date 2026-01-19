#!/usr/bin/env pwsh
# Script para criar release automaticamente no GitHub
# Uso: .\create-release.ps1 -Token "seu_github_token"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "v1.0.0",
    
    [Parameter(Mandatory=$false)]
    [string]$RepoOwner = "lopesleo",
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "Discord-Lite"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Creating GitHub Release for $Version..." -ForegroundColor Cyan

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
    Write-Host "❌ Arquivo $zipFile não encontrado!" -ForegroundColor Red
    Write-Host "📦 Criando arquivo zip..." -ForegroundColor Yellow
    
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
    
    Write-Host "✅ Arquivo zip criado!" -ForegroundColor Green
}

# Corpo do release
$releaseBody = @"
## 🎮 Discord Lite for Steam Deck

Complete Discord voice chat integration for Steam Deck via Decky Loader.

### ✨ Features
- 🎤 Full voice chat controls (mute, deafen, join/leave)
- 🔊 Per-user volume control with memory
- 📢 Server and channel browsing
- 👥 Member list with speaking indicators
- ⏱️ Call timer
- 🔔 Toast notifications for voice events
- 🔗 Auto-connect option
- 🌐 Multi-language support (EN/PT)
- 🎨 Professional Discord-themed UI

### 📋 Requirements
- Steam Deck with [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
- Discord desktop app (Flatpak recommended)

### 🚀 Installation
1. Download ``Discord-Lite-$Version.zip``
2. Extract to ``~/homebrew/plugins/``
3. Restart Decky Loader

### 📖 Usage
See [README.md](https://github.com/$RepoOwner/$RepoName#readme) for detailed instructions.

### 🔒 Security Note
This plugin uses Discord RPC with OAuth2. Your credentials are stored locally and never shared. The CLIENT_SECRET in the code is safe for local RPC applications as explained in the [Discord OAuth2 documentation](https://discord.com/developers/docs/topics/oauth2).
"@

# Criar o release
Write-Host "📝 Creating release $Version..." -ForegroundColor Yellow

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
    
    Write-Host "✅ Release criado com sucesso!" -ForegroundColor Green
    Write-Host "🔗 URL: $($release.html_url)" -ForegroundColor Cyan
    
    # Upload do arquivo zip
    Write-Host "📤 Uploading $zipFile..." -ForegroundColor Yellow
    
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
    
    Write-Host "✅ Arquivo enviado com sucesso!" -ForegroundColor Green
    Write-Host "📦 Download: $($asset.browser_download_url)" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "🎉 Release $Version publicado com sucesso!" -ForegroundColor Green
    Write-Host "🔗 $($release.html_url)" -ForegroundColor Cyan
    
} catch {
    Write-Host "❌ Erro ao criar release:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        $errorJson = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "Detalhes: $($errorJson.message)" -ForegroundColor Red
    }
    
    exit 1
}
