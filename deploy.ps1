# Discord Lite - Deploy Script for Steam Deck
# Usage: .\deploy.ps1
# Optional: .\deploy.ps1 -SkipBuild  (to deploy without rebuilding)

param(
    [switch]$SkipBuild
)

# Configuration
$DECK_IP = "192.168.1.129"
$DECK_USER = "deck"
$DECK_PORT = "22"
$PLUGIN_NAME = "Discord-Lite"
$PLUGIN_PATH = "/home/deck/homebrew/plugins/$PLUGIN_NAME"

# Colors for output
function Write-ColorOutput($Color, $Message) {
    Write-Host $Message -ForegroundColor $Color
}

Write-ColorOutput Cyan "=========================================="
Write-ColorOutput Cyan "   Discord Lite - Deploy to Steam Deck"
Write-ColorOutput Cyan "=========================================="
Write-Host ""

# Step 1: Build (unless skipped)
if (-not $SkipBuild) {
    Write-ColorOutput Yellow "[1/4] Building plugin..."
    pnpm run build
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "Build failed!"
        exit 1
    }
    Write-ColorOutput Green "Build successful!"
} else {
    Write-ColorOutput Yellow "[1/4] Skipping build..."
}

# Step 2: Test SSH connection
Write-ColorOutput Yellow "[2/4] Testing connection to Steam Deck..."
$sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes "${DECK_USER}@${DECK_IP}" "echo OK" 2>&1
if ($sshTest -ne "OK") {
    Write-ColorOutput Red "Cannot connect to Steam Deck at $DECK_IP"
    Write-ColorOutput Red "Make sure:"
    Write-ColorOutput Red "  1. Steam Deck is on and connected to the network"
    Write-ColorOutput Red "  2. SSH is enabled (Settings > Developer Options)"
    Write-ColorOutput Red "  3. SSH key is configured or you'll need to enter password"
    Write-Host ""
    Write-ColorOutput Yellow "Trying with password authentication..."
}

# Step 3: Deploy files
Write-ColorOutput Yellow "[3/4] Deploying files to Steam Deck..."

# Create temp directory on deck
ssh "${DECK_USER}@${DECK_IP}" "mkdir -p /tmp/discord-lite-deploy"

# Copy all files to temp directory
Write-ColorOutput Cyan "  Copying files to Steam Deck..."
scp -r "dist" "main.py" "plugin.json" "package.json" "lib" "defaults" "${DECK_USER}@${DECK_IP}:/tmp/discord-lite-deploy/"

# Run all sudo commands in a single SSH session (only one password prompt)
Write-ColorOutput Cyan "  Installing plugin..."
ssh -t "${DECK_USER}@${DECK_IP}" "sudo systemctl stop plugin_loader 2>/dev/null || true; sudo rm -rf $PLUGIN_PATH; sudo mkdir -p $PLUGIN_PATH; sudo cp -r /tmp/discord-lite-deploy/* $PLUGIN_PATH/; sudo chown -R deck:deck $PLUGIN_PATH; sudo chmod -R 755 $PLUGIN_PATH; rm -rf /tmp/discord-lite-deploy; echo 'Plugin installed!'"

Write-ColorOutput Green "Files deployed!"

# Step 4: Restart Decky Loader
Write-ColorOutput Yellow "[4/4] Restarting Decky Loader..."
ssh -t "${DECK_USER}@${DECK_IP}" "sudo systemctl start plugin_loader"

Write-Host ""
Write-ColorOutput Green "=========================================="
Write-ColorOutput Green "   Deploy Complete!"
Write-ColorOutput Green "=========================================="
Write-ColorOutput Cyan "Plugin deployed to: $PLUGIN_PATH"
Write-ColorOutput Cyan "Steam Deck IP: $DECK_IP"
Write-Host ""
