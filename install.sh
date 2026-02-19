#!/bin/bash
# install.sh — Install the Chrome Native Messaging host on macOS or Linux
set -e

HOST_NAME="com.propdream.keystroke_sender"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_PATH="$SCRIPT_DIR/keystroke_sender.py"

# Detect OS and set manifest directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
elif [[ "$OSTYPE" == "linux"* ]]; then
    TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
else
    echo "Unsupported OS: $OSTYPE"
    echo "Use install.bat for Windows."
    exit 1
fi

# Prompt for Chrome extension ID
echo "Enter your Chrome extension ID (found at chrome://extensions):"
read -r EXTENSION_ID

if [ -z "$EXTENSION_ID" ]; then
    echo "Error: Extension ID cannot be empty."
    exit 1
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# Write the native messaging host manifest
cat > "$TARGET_DIR/$HOST_NAME.json" << EOF
{
  "name": "$HOST_NAME",
  "description": "Simulates OS-level keystrokes for Chrome Form Filler",
  "path": "$HOST_PATH",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF

# Make the host script executable
chmod +x "$HOST_PATH"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "Native messaging host '$HOST_NAME' installed successfully."
echo "  Manifest: $TARGET_DIR/$HOST_NAME.json"
echo "  Host:     $HOST_PATH"
echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "IMPORTANT: On macOS, you must grant Accessibility permission to your"
    echo "terminal/Python in System Preferences > Privacy & Security > Accessibility."
fi
