#!/bin/bash

# ==========================================
# Script de Build para Decky Plugin (WSL/Linux)
# ==========================================

VERSION="v1.0.0"
PLUGIN_NAME="DiscordLite"
ZIP_FILE="Discord-Lite-${VERSION}.zip"
BUILD_DIR="./temp_build"
TARGET_DIR="${BUILD_DIR}/${PLUGIN_NAME}"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Building ${PLUGIN_NAME} ${VERSION} via WSL...${NC}"

# 1. Limpeza Inicial
# ------------------------------------------
if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
fi
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
fi

mkdir -p "$TARGET_DIR"

# 2. Copiar Arquivos
# ------------------------------------------
echo -e "${YELLOW}Copying files...${NC}"

# Copia tudo, MAS exclui arquivos de sistema, git, node_modules, etc.
# Usamos rsync que é mais inteligente que o cp para exclusões
rsync -av --progress . "$TARGET_DIR" \
    --exclude '.git' \
    --exclude '.github' \
    --exclude '.vscode' \
    --exclude 'node_modules' \
    --exclude 'src' \
    --exclude '__pycache__' \
    --exclude '*.zip' \
    --exclude 'temp_build' \
    --exclude 'build.sh' \
    --exclude '*.ps1' \
    --quiet

# 3. Limpeza de Lixo (Python Cache e arquivos Mac/Windows)
# ------------------------------------------
echo -e "${YELLOW}Cleaning binaries and temp files...${NC}"
find "$TARGET_DIR" -type d -name "__pycache__" -exec rm -rf {} +
find "$TARGET_DIR" -name ".DS_Store" -delete
find "$TARGET_DIR" -name "Thumbs.db" -delete

# 4. FIX CRUCIAL: Permissões e Line Endings
# ------------------------------------------
# Este é o segredo para funcionar no Deck
echo -e "${YELLOW}Fixing Permissions and Line Endings (CRLF -> LF)...${NC}"

# Garante que main.py é executável
chmod +x "$TARGET_DIR/main.py"

# Converte quebras de linha Windows (CRLF) para Linux (LF)
# Requer o pacote 'dos2unix'. Se não tiver, o script avisa mas tenta continuar.
if command -v dos2unix &> /dev/null; then
    find "$TARGET_DIR" -name "*.py" -exec dos2unix {} \;
    find "$TARGET_DIR" -name "*.json" -exec dos2unix {} \;
    find "$TARGET_DIR" -name "*.sh" -exec dos2unix {} \;
else
    echo -e "${YELLOW}Warning: 'dos2unix' not found. Ensure your files are saved as LF in VS Code.${NC}"
fi

# 5. Compactação
# ------------------------------------------
echo -e "${YELLOW}Compressing package...${NC}"

# Entra na pasta temp para zipar a pasta 'DiscordLite'
cd "$BUILD_DIR"
zip -r -q "../$ZIP_FILE" "$PLUGIN_NAME"
cd ..

# 6. Limpeza Final e Resultado
# ------------------------------------------
rm -rf "$BUILD_DIR"

FILE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)

echo -e ""
echo -e "${GREEN}SUCCESS! Package created.${NC}"
echo -e "-----------------------------------"
echo -e "File: ${CYAN}${ZIP_FILE}${NC}"
echo -e "Size: ${CYAN}${FILE_SIZE}${NC}"
echo -e "-----------------------------------"
echo -e "To install on Steam Deck:"
echo -e "1. Copy ${ZIP_FILE} to the Deck."
echo -e "2. Extract to ${CYAN}~/homebrew/plugins/${NC}"
echo -e "   (Since we ran chmod +x, it should work instantly!)"
echo -e ""