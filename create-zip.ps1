# Script para criar o arquivo zip do plugin para instalacao no Steam Deck
# Uso: .\create-zip.ps1 [-Version "v1.0.0"]

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "v1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "Creating Discord Lite package $Version..." -ForegroundColor Cyan

# Nome do arquivo zip
$zipFile = "Discord-Lite-$Version.zip"
$zipPath = Join-Path $PSScriptRoot $zipFile

# Remover zip antigo se existir
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "Old zip removed" -ForegroundColor Yellow
}

# Criar temp folder
$tempDir = Join-Path $PSScriptRoot "temp_release"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

Write-Host "Copying files..." -ForegroundColor Yellow

# Copiar arquivos essenciais
$files = @('main.py', 'plugin.json', 'package.json', 'README.md', 'LICENSE')
foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $tempDir
        Write-Host "  + $file" -ForegroundColor Gray
    } else {
        Write-Host "  ! $file not found" -ForegroundColor Yellow
    }
}

# Copiar pastas
$folders = @('dist', 'defaults', 'assets')
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Copy-Item $folder -Destination $tempDir -Recurse -Force
        $fileCount = (Get-ChildItem "$tempDir\$folder" -Recurse -File).Count
        Write-Host "  + $folder/ ($fileCount files)" -ForegroundColor Gray
    } else {
        Write-Host "  ! $folder/ not found" -ForegroundColor Yellow
    }
}

# Copiar lib (sem __pycache__)
if (Test-Path "lib") {
    Copy-Item "lib" -Destination $tempDir -Recurse -Force
    
    # Remover __pycache__ e arquivos temporarios
    $removed = 0
    Get-ChildItem -Path "$tempDir\lib" -Recurse -Force | Where-Object { 
        $_.Name -eq '__pycache__' -or 
        $_.Extension -eq '.pyc' -or 
        $_.Name -eq '.DS_Store' -or
        $_.Name -eq 'Thumbs.db'
    } | ForEach-Object {
        if (Test-Path $_.FullName) {
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            $removed++
        }
    }
    
    $fileCount = (Get-ChildItem "$tempDir\lib" -Recurse -File).Count
    Write-Host "  + lib/ ($fileCount files)" -ForegroundColor Gray
    if ($removed -gt 0) {
        Write-Host "    Cleaned $removed temp files" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "Compressing..." -ForegroundColor Yellow

# Criar zip com os arquivos da pasta temp (sem incluir a pasta temp em si)
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal -Force

# Limpar temp
Remove-Item $tempDir -Recurse -Force

# Mostrar informacoes do zip
$zipInfo = Get-Item $zipPath
$zipSizeMB = [math]::Round($zipInfo.Length / 1MB, 2)

Write-Host ""
Write-Host "Package created successfully!" -ForegroundColor Green
Write-Host "File: $zipFile" -ForegroundColor Cyan
Write-Host "Size: $zipSizeMB MB" -ForegroundColor Cyan
Write-Host ""
Write-Host "Installation instructions:" -ForegroundColor Yellow
Write-Host "  1. Copy file to Steam Deck" -ForegroundColor Gray
Write-Host "  2. Extract to: ~/homebrew/plugins/DiscordLite/" -ForegroundColor Gray
Write-Host "  3. Restart Decky Loader" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use deploy script: .\deploy.ps1" -ForegroundColor Yellow
