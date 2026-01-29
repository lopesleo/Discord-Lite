#!/bin/bash

# ==========================================
# Script de Build para Decky Plugin (WSL/Linux)
# ==========================================

# Detectar versão automaticamente do plugin.json
if [ -f "plugin.json" ]; then
    VERSION=$(grep '"version"' plugin.json | sed 's/.*"version": "\([^"]*\)".*/v\1/')
else
    VERSION="v1.0.0"
fi

PLUGIN_NAME="DiscordLite"
ZIP_FILE="Discord-Lite-${VERSION}.zip"
BUILD_DIR="./temp_build"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Building ${PLUGIN_NAME} ${VERSION} via WSL...${NC}"

# 1. Code Verification
# ------------------------------------------
echo -e "${YELLOW}Verifying code integrity...${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Warning: Python3 not found. Skipping code verification.${NC}"
else
    # Compile main.py to check for syntax errors
    if ! python3 -m py_compile main.py 2>/dev/null; then
        echo -e "\033[0;31mERROR: main.py has syntax errors!${NC}"
        exit 1
    fi
    echo "  ✓ main.py compiled successfully"

    # Compile all backend modules
    if [ -d "backend" ]; then
        if ! python3 -m compileall -q backend/ 2>/dev/null; then
            echo -e "\033[0;31mERROR: Backend modules have syntax errors!${NC}"
            exit 1
        fi
        echo "  ✓ Backend modules compiled successfully"

        # Check for problematic decky imports in backend
        if grep -r "^import decky\|^from decky" backend/ >/dev/null 2>&1; then
            echo -e "\033[0;31mERROR: Backend modules should not import decky at module level!${NC}"
            echo -e "\033[0;31mUse dependency injection instead.${NC}"
            exit 1
        fi
        echo "  ✓ No problematic decky imports found"
    fi

    echo -e "${GREEN}Code verification passed!${NC}"
fi

# 2. Limpeza Inicial
# ------------------------------------------
if [ -d "$BUILD_DIR" ]; then
    rm -rf "$BUILD_DIR"
fi
if [ -f "$ZIP_FILE" ]; then
    rm "$ZIP_FILE"
fi

# Criar pasta com nome do plugin dentro do BUILD_DIR
# Estrutura: temp_build/DiscordLite/arquivos...
mkdir -p "$BUILD_DIR/$PLUGIN_NAME"

# 3. Copiar Arquivos (dentro da pasta do plugin)
# ------------------------------------------
echo -e "${YELLOW}Copying files...${NC}"

# Lista de arquivos essenciais
files=("main.py" "plugin.json" "package.json" "README.md" "LICENSE")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BUILD_DIR/$PLUGIN_NAME/"
        echo "  + $file"
    fi
done

# Copiar pastas
folders=("dist" "defaults" "assets" "lib" "backend")
for folder in "${folders[@]}"; do
    if [ -d "$folder" ]; then
        cp -r "$folder" "$BUILD_DIR/$PLUGIN_NAME/"
        file_count=$(find "$BUILD_DIR/$PLUGIN_NAME/$folder" -type f | wc -l)
        echo "  + $folder/ ($file_count files)"
    fi
done

# 4. Limpeza de Lixo (Python Cache e arquivos Mac/Windows)
# ------------------------------------------
echo -e "${YELLOW}Cleaning binaries and temp files...${NC}"
find "$BUILD_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BUILD_DIR" -name ".DS_Store" -delete 2>/dev/null || true
find "$BUILD_DIR" -name "Thumbs.db" -delete 2>/dev/null || true
find "$BUILD_DIR" -name "*.pyc" -delete 2>/dev/null || true

# 5. FIX CRUCIAL: Permissões e Line Endings
# ------------------------------------------
echo -e "${YELLOW}Fixing Permissions and Line Endings (CRLF -> LF)...${NC}"

# Garante que main.py é executável
chmod +x "$BUILD_DIR/$PLUGIN_NAME/main.py"

# Converte quebras de linha Windows (CRLF) para Linux (LF)
if command -v dos2unix &> /dev/null; then
    find "$BUILD_DIR" -name "*.py" -exec dos2unix {} \; 2>/dev/null || true
    find "$BUILD_DIR" -name "*.json" -exec dos2unix {} \; 2>/dev/null || true
    find "$BUILD_DIR" -name "*.sh" -exec dos2unix {} \; 2>/dev/null || true
else
    echo -e "${YELLOW}Warning: 'dos2unix' not found. Ensure your files are saved as LF in VS Code.${NC}"
fi

# 6. Compactação (com pasta do plugin na raiz do zip)
# ------------------------------------------
echo -e "${YELLOW}Compressing package...${NC}"

# Compacta incluindo a pasta DiscordLite na raiz do ZIP
cd "$BUILD_DIR"
zip -r -q "../$ZIP_FILE" "$PLUGIN_NAME"
cd ..

# 7. Limpeza Final e Resultado
# ------------------------------------------
rm -rf "$BUILD_DIR"

FILE_SIZE=$(du -h "$ZIP_FILE" | cut -f1)

echo -e ""
echo -e "${GREEN}SUCCESS! Package created.${NC}"
echo -e "-----------------------------------"
echo -e "File: ${CYAN}${ZIP_FILE}${NC}"
echo -e "Size: ${CYAN}${FILE_SIZE}${NC}"
echo -e "Structure: ${CYAN}${PLUGIN_NAME}/...${NC}"
echo -e "-----------------------------------"
echo -e "To install on Steam Deck:"
echo -e "1. Copy ${ZIP_FILE} to the Deck."
echo -e "2. Install via Decky Loader or extract to ${CYAN}~/homebrew/plugins/${NC}"
