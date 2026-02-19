#!/bin/bash
# uninstall.sh — Remove the Chrome Native Messaging host on macOS or Linux
set -e

HOST_NAME="com.propdream.keystroke_sender"

if [[ "$OSTYPE" == "darwin"* ]]; then
    TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
elif [[ "$OSTYPE" == "linux"* ]]; then
    TARGET_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

MANIFEST="$TARGET_DIR/$HOST_NAME.json"

if [ -f "$MANIFEST" ]; then
    rm -f "$MANIFEST"
    echo "Native messaging host '$HOST_NAME' uninstalled."
    echo "  Removed: $MANIFEST"
else
    echo "Manifest not found at $MANIFEST — nothing to remove."
fi
