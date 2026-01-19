# Script para criar o arquivo zip do plugin para Decky Loader e fazer deploy
# Uso: .\deploy.ps1 [-Version "v1.0.0"] [-Deploy]

param(
    [Parameter(Mandatory=$false)]
    [string]$Version = "v1.0.0",
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"

# --- CONFIGURAÇÕES ---
# Nome da pasta que ficará DENTRO do zip (importante para o Decky)
$PluginFolder = "DiscordLite" 
# Nome do arquivo final
$ZipFile = "Discord-Lite-$Version.zip"

# Configurações do Steam Deck
$DeckIP = "192.168.1.129"
$DeckUser = "deck"
$DeckPluginPath = "/home/deck/homebrew/plugins/$PluginFolder"
$RemoteZipPath = "/home/deck/plugin.zip"

Write-Host " Building package for $PluginFolder ($Version)..." -ForegroundColor Cyan

# Definir caminhos
$ZipPath = Join-Path $PSScriptRoot $ZipFile
$TempRoot = Join-Path $PSScriptRoot "temp_release"

# 1. Limpeza inicial
# Remover zip antigo
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
    Write-Host " [OK] Old zip removed" -ForegroundColor DarkGray
}

# Recriar pasta temporária limpa
if (Test-Path $TempRoot) { Remove-Item $TempRoot -Recurse -Force }
New-Item -ItemType Directory -Path $TempRoot | Out-Null

Write-Host " Copying files..." -ForegroundColor Yellow

# 2. Copiar Arquivos da Raiz
$files = @('main.py', 'plugin.json', 'package.json', 'README.md', 'LICENSE')
foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $TempRoot
        Write-Host "   + $file" -ForegroundColor Gray
    } else {
        Write-Host "   ! $file not found (Skipping)" -ForegroundColor DarkYellow
    }
}

# 3. Copiar Pastas (Assets, Dist, Defaults)
$folders = @('dist', 'defaults', 'assets')
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        Copy-Item $folder -Destination $TempRoot -Recurse -Force
        $count = (Get-ChildItem "$TempRoot\$folder" -Recurse -File).Count
        Write-Host "   + $folder/ ($count files)" -ForegroundColor Gray
    }
}

# 4. Copiar Libs (com limpeza de lixo)
if (Test-Path "lib") {
    Copy-Item "lib" -Destination $TempRoot -Recurse -Force
    
    # Remover __pycache__, .pyc, .DS_Store, etc.
    $removedCount = 0
    Get-ChildItem -Path "$TempRoot\lib" -Recurse -Force | Where-Object { 
        $_.Name -eq '__pycache__' -or 
        $_.Extension -eq '.pyc' -or 
        $_.Name -eq '.DS_Store' -or
        $_.Name -eq 'Thumbs.db'
    } | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        $removedCount++
    }
    
    $libCount = (Get-ChildItem "$TempRoot\lib" -Recurse -File).Count
    Write-Host "   + lib/ ($libCount files, cleaned $removedCount temp items)" -ForegroundColor Gray
}

# 5. Compactação
Write-Host ""
Write-Host " Compressing..." -ForegroundColor Yellow

# Compacta o conteúdo de temp_release (arquivos na raiz)
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
Write-Host " 2. Extract into: ~/homebrew/plugins/$PluginFolder/"
Write-Host ""Write-Host " Done!" -ForegroundColor Green

# Deploy se solicitado
if ($Deploy) {
    Write-Host ""
    Write-Host " Deploying to Steam Deck..." -ForegroundColor Cyan
    
    # Copiar zip para o Deck
    Write-Host " Copying zip to Steam Deck..." -ForegroundColor Yellow
    & scp $ZipPath "${DeckUser}@${DeckIP}:${RemoteZipPath}"
    if ($LASTEXITCODE -ne 0) { throw "Failed to copy zip to Steam Deck" }
    
    # Instalar no Deck
    Write-Host " Installing plugin..." -ForegroundColor Yellow
    $installCommand = @"
sudo systemctl stop plugin_loader 2>/dev/null || true
sudo rm -rf $DeckPluginPath
sudo mkdir -p $DeckPluginPath
sudo unzip -q -o $RemoteZipPath -d $DeckPluginPath
sudo chown -R ${DeckUser}:${DeckUser} $DeckPluginPath
sudo systemctl restart plugin_loader
"@
    
    & ssh -t "${DeckUser}@${DeckIP}" $installCommand
    if ($LASTEXITCODE -ne 0) { throw "Failed to install plugin on Steam Deck" }
    
    Write-Host " Deployment completed!" -ForegroundColor Green
}