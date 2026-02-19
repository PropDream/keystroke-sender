#!/usr/bin/env python3
"""
Register (or unregister) the Chrome Native Messaging host manifest.

Usage:
  keystroke-sender-register <extension-id>
  keystroke-sender-register --unregister
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HOST_NAME = "com.propdream.keystroke_sender"


def _manifest_dir():
    """Return the platform-specific directory for Chrome native messaging manifests."""
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        )
    elif sys.platform == "linux":
        return os.path.expanduser(
            "~/.config/google-chrome/NativeMessagingHosts"
        )
    elif sys.platform == "win32":
        return os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Google", "Chrome", "User Data", "NativeMessagingHosts",
        )
    else:
        sys.exit(f"Unsupported platform: {sys.platform}")


def _host_executable():
    """Find the installed keystroke-sender console script."""
    path = shutil.which("keystroke-sender")
    if path is None:
        sys.exit(
            "Error: 'keystroke-sender' not found on PATH.\n"
            "Install the package first: pip install keystroke-sender"
        )
    return os.path.abspath(path)


def register(extension_id):
    """Write the native messaging host manifest and (on Windows) the registry key."""
    manifest_dir = _manifest_dir()
    os.makedirs(manifest_dir, exist_ok=True)

    host_path = _host_executable()

    # On Windows, Chrome expects a .bat or .exe — the pip console_script is an .exe
    manifest = {
        "name": HOST_NAME,
        "description": "Simulates OS-level keystrokes for Chrome Form Filler",
        "path": host_path,
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }

    manifest_path = os.path.join(manifest_dir, f"{HOST_NAME}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Manifest written to: {manifest_path}")
    print(f"Host executable:     {host_path}")

    # Windows requires a registry key pointing to the manifest
    if sys.platform == "win32":
        reg_key = rf"HKCU\Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        subprocess.run(
            ["reg", "add", reg_key, "/ve", "/t", "REG_SZ", "/d", manifest_path, "/f"],
            check=True,
        )
        print(f"Registry key:        {reg_key}")

    print()
    print(f"Native messaging host '{HOST_NAME}' registered successfully.")

    if sys.platform == "darwin":
        print()
        print("IMPORTANT: On macOS, grant Accessibility permission to your")
        print("terminal/Python in System Preferences > Privacy & Security > Accessibility.")


def unregister():
    """Remove the native messaging host manifest and (on Windows) the registry key."""
    manifest_dir = _manifest_dir()
    manifest_path = os.path.join(manifest_dir, f"{HOST_NAME}.json")

    if os.path.exists(manifest_path):
        os.remove(manifest_path)
        print(f"Removed manifest: {manifest_path}")
    else:
        print(f"Manifest not found: {manifest_path}")

    if sys.platform == "win32":
        reg_key = rf"HKCU\Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
        subprocess.run(
            ["reg", "delete", reg_key, "/f"],
            check=False,  # OK if key doesn't exist
        )
        print(f"Removed registry key: {reg_key}")

    print(f"Native messaging host '{HOST_NAME}' unregistered.")


def main():
    parser = argparse.ArgumentParser(
        description="Register the keystroke-sender Chrome Native Messaging host."
    )
    parser.add_argument(
        "extension_id",
        nargs="?",
        help="Chrome extension ID (find it at chrome://extensions)",
    )
    parser.add_argument(
        "--unregister",
        action="store_true",
        help="Remove the native messaging host registration",
    )
    args = parser.parse_args()

    if args.unregister:
        unregister()
    elif args.extension_id:
        register(args.extension_id)
    else:
        # Interactive prompt
        ext_id = input("Enter your Chrome extension ID (found at chrome://extensions): ").strip()
        if not ext_id:
            sys.exit("Error: Extension ID cannot be empty.")
        register(ext_id)


if __name__ == "__main__":
    main()
