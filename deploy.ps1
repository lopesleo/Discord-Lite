# Script para criar o arquivo zip do plugin para Decky Loader
# Uso: .\create-zip.ps1 [-Version "v1.0.0"]

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "v1.0.0"
)

$ErrorActionPreference = "Stop"

# --- CONFIGURAÇÕES ---
# Nome da pasta que ficará DENTRO do zip (importante para o Decky)
$PluginFolder = "DiscordLite" 
# Nome do arquivo final
$ZipFile = "Discord-Lite-$Version.zip"

Write-Host " Building package for $PluginFolder ($Version)..." -ForegroundColor Cyan

# Definir caminhos
$ZipPath = Join-Path $PSScriptRoot $ZipFile
$TempRoot = Join-Path $PSScriptRoot "temp_release"
$TargetDir = Join-Path $TempRoot $PluginFolder

# 1. Limpeza inicial
# Remover zip antigo
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
    Write-Host " [OK] Old zip removed" -ForegroundColor DarkGray
}

# Recriar pasta temporária limpa (temp_release/DiscordLite)
if (Test-Path $TempRoot) { Remove-Item $TempRoot -Recurse -Force }
New-Item -ItemType Directory -Path $TargetDir | Out-Null

Write-Host " Copying files..." -ForegroundColor Yellow

# 2. Copiar Arquivos da Raiz
$files = @('main.py', 'plugin.json', 'package.json', 'README.md', 'LICENSE')
foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $TargetDir
        Write-Host "   + $file" -ForegroundColor Gray
    } else {
        Write-Host "   ! $file not found (Skipping)" -ForegroundColor DarkYellow
    }
}

# 3. Copiar Pastas (Assets, Dist, Defaults)
$folders = @('dist', 'defaults', 'assets')
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Copy-Item $folder -Destination $TargetDir -Recurse -Force
        $count = (Get-ChildItem "$TargetDir\$folder" -Recurse -File).Count
        Write-Host "   + $folder/ ($count files)" -ForegroundColor Gray
    }
}

# 4. Copiar Libs (com limpeza de lixo)
if (Test-Path "lib") {
    Copy-Item "lib" -Destination $TargetDir -Recurse -Force
    
    # Remover __pycache__, .pyc, .DS_Store, etc.
    $removedCount = 0
    Get-ChildItem -Path "$TargetDir\lib" -Recurse -Force | Where-Object { 
        $_.Name -eq '__pycache__' -or 
        $_.Extension -eq '.pyc' -or 
        $_.Name -eq '.DS_Store' -or
        $_.Name -eq 'Thumbs.db'
    } | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        $removedCount++
    }
    
    $libCount = (Get-ChildItem "$TargetDir\lib" -Recurse -File).Count
    Write-Host "   + lib/ ($libCount files, cleaned $removedCount temp items)" -ForegroundColor Gray
}

# 5. Compactação
Write-Host ""
Write-Host " Compressing..." -ForegroundColor Yellow

# Compacta o conteúdo de temp_release (que contem a pasta DiscordLite)
# Isso garante que ao abrir o zip, o usuário veja a pasta, e não os arquivos soltos.
Compress-Archive -Path "$TempRoot\*" -DestinationPath $ZipPath -CompressionLevel Optimal -Force

# 6. Limpeza Final
Remove-Item $TempRoot -Recurse -Force

# 7. Relatório
$ZipInfo = Get-Item $ZipPath
$SizeMB = [math]::Round($ZipInfo.Length / 1MB, 2)

Write-Host ""
Write-Host "SUCCESS! Package created." -ForegroundColor Green
Write-Host "---------------------------------------------------" -ForegroundColor DarkGray
Write-Host " File:  $ZipFile"
Write-Host " Path:  $ZipPath"
Write-Host " Size:  $SizeMB MB"
Write-Host "---------------------------------------------------" -ForegroundColor DarkGray
Write-Host "INSTALLATION:" -ForegroundColor Cyan
Write-Host " 1. Copy zip to Steam Deck."
Write-Host " 2. Extract into: ~/homebrew/plugins/"
Write-Host "    (The zip already contains the '$PluginFolder' folder)"
Write-Host ""Write-Host " Done!" -ForegroundColor Green