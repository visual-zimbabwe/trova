#!/usr/bin/env bash
set -e

# Styled output for Omarchy Linux
BOLD="\033[1m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
CYAN="\033[1;36m"
RESET="\033[0m"

echo -e "\n${BOLD}${CYAN}==> Setting up Trova for Omarchy Linux...${RESET}"

APP_DIR="$HOME/.local/share/trova-app"
VENV_DIR="$HOME/apps/trova"
REPO_URL="https://github.com/visual-zimbabwe/trova.git"

# Determine source: local cloned repo or curl pipe
if [ -f "backend/desktop.py" ] && [ -d "frontend" ]; then
    SOURCE_DIR="$(pwd)"
    echo -e "${YELLOW}• Installing from local directory:${RESET} $SOURCE_DIR"
elif [ -n "${BASH_SOURCE[0]}" ] && [ -f "$(dirname "${BASH_SOURCE[0]}")/backend/desktop.py" ]; then
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${YELLOW}• Installing from repository:${RESET} $SOURCE_DIR"
else
    # Piped via curl - clone or pull latest to ~/.local/share/trova-app
    echo -e "${YELLOW}• Fetching latest Trova release...${RESET}"
    mkdir -p "$HOME/.local/share"
    if [ -d "$APP_DIR/.git" ]; then
        echo -e "${YELLOW}• Updating existing installation in $APP_DIR...${RESET}"
        git -C "$APP_DIR" pull --quiet
    else
        echo -e "${YELLOW}• Cloning into $APP_DIR...${RESET}"
        rm -rf "$APP_DIR"
        git clone --depth 1 "$REPO_URL" "$APP_DIR" --quiet
    fi
    SOURCE_DIR="$APP_DIR"
fi

# Ensure Python virtual environment with system packages bridge (for WebKitGTK / GObject)
echo -e "${YELLOW}• Configuring Python environment...${RESET}"
mkdir -p "$HOME/apps"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
mkdir -p "$VENV_DIR/lib/python$PY_VER/site-packages"
echo "/usr/lib/python$PY_VER/site-packages" > "$VENV_DIR/lib/python$PY_VER/site-packages/system_packages.pth"

"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install pywebview websockets requests --quiet

# Install desktop launcher, icons, and desktop entry
echo -e "${YELLOW}• Registering launcher and desktop entry...${RESET}"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"

ln -sf "$SOURCE_DIR/bin/trova" "$HOME/.local/bin/trova"

if [ -f "$SOURCE_DIR/assets/trova.svg" ]; then
    cp "$SOURCE_DIR/assets/trova.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/trova.svg"
fi
if [ -f "$SOURCE_DIR/assets/trova.png" ]; then
    cp "$SOURCE_DIR/assets/trova.png" "$HOME/.local/share/icons/hicolor/256x256/apps/trova.png"
fi

cat << DESKTOP_EOF > "$HOME/.local/share/applications/trova.desktop"
[Desktop Entry]
Name=Trova
GenericName=Where to Stream
Comment=Global Streaming Availability for Movies and TV Shows
Exec=$HOME/.local/bin/trova %F
Icon=trova
Terminal=false
Type=Application
Categories=AudioVideo;Video;Network;
StartupWMClass=trova
Keywords=movie;film;streaming;netflix;prime;max;paramount;trova;cinema;where to watch;where to stream;
DESKTOP_EOF

# Clean up legacy .desktop files
rm -f "$HOME/.local/share/applications/OmaTrova.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo -e "\n${BOLD}${GREEN}✓ Trova installation complete!${RESET}"
echo -e "  Launch anytime by running: ${BOLD}${CYAN}trova${RESET}"
echo -e "  Or find ${BOLD}Trova${RESET} in your Omarchy application menu.\n"
