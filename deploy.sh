#!/bin/bash
# Discord Lite - Deploy Script for Steam Deck
# Usage: ./deploy.sh
# Optional: ./deploy.sh --skip-build (to deploy without rebuilding)

# Configuration
DECK_IP="192.168.1.129"
DECK_USER="deck"
PLUGIN_NAME="Discord-Lite"
PLUGIN_PATH="/home/deck/homebrew/plugins/$PLUGIN_NAME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=========================================="
echo -e "   Discord Lite - Deploy to Steam Deck"
echo -e "==========================================${NC}"
echo ""

# Step 1: Build
if [[ "$1" != "--skip-build" ]]; then
    echo -e "${YELLOW}[1/4] Building plugin...${NC}"
    pnpm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}Build failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}Build successful!${NC}"
else
    echo -e "${YELLOW}[1/4] Skipping build...${NC}"
fi

# Step 2: Test connection
echo -e "${YELLOW}[2/4] Testing connection to Steam Deck...${NC}"
if ! ssh -o ConnectTimeout=5 -o BatchMode=yes ${DECK_USER}@${DECK_IP} "echo OK" 2>/dev/null; then
    echo -e "${YELLOW}Connection requires password or key not set up.${NC}"
fi

# Step 3: Deploy
echo -e "${YELLOW}[3/4] Deploying files...${NC}"

ssh -t ${DECK_USER}@${DECK_IP} "
    sudo systemctl stop plugin_loader 2>/dev/null || true
    sudo rm -rf ${PLUGIN_PATH}
    sudo mkdir -p ${PLUGIN_PATH}/dist
    sudo mkdir -p ${PLUGIN_PATH}/lib
    sudo mkdir -p ${PLUGIN_PATH}/defaults
"

echo -e "${CYAN}  Copying files...${NC}"
scp dist/index.js ${DECK_USER}@${DECK_IP}:/tmp/
scp main.py plugin.json package.json ${DECK_USER}@${DECK_IP}:/tmp/
scp -r lib ${DECK_USER}@${DECK_IP}:/tmp/
scp -r defaults ${DECK_USER}@${DECK_IP}:/tmp/

ssh -t ${DECK_USER}@${DECK_IP} "
    sudo cp /tmp/index.js ${PLUGIN_PATH}/dist/
    sudo cp /tmp/main.py /tmp/plugin.json /tmp/package.json ${PLUGIN_PATH}/
    sudo cp -r /tmp/lib/* ${PLUGIN_PATH}/lib/
    sudo cp -r /tmp/defaults/* ${PLUGIN_PATH}/defaults/
    sudo chown -R deck:deck ${PLUGIN_PATH}
    sudo chmod -R 755 ${PLUGIN_PATH}
    rm -rf /tmp/index.js /tmp/main.py /tmp/plugin.json /tmp/package.json /tmp/lib /tmp/defaults
"

echo -e "${GREEN}Files deployed!${NC}"

# Step 4: Restart
echo -e "${YELLOW}[4/4] Restarting Decky Loader...${NC}"
ssh -t ${DECK_USER}@${DECK_IP} "sudo systemctl start plugin_loader"

echo ""
echo -e "${GREEN}=========================================="
echo -e "   Deploy Complete!"
echo -e "==========================================${NC}"
echo -e "${CYAN}Plugin deployed to: ${PLUGIN_PATH}${NC}"
