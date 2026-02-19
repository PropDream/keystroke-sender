# Keystroke Sender

A Chrome Native Messaging host that simulates OS-level keystrokes. Receives text strings from a Chrome extension and types them out as real key presses using `pynput`.

Works on **macOS**, **Linux**, and **Windows**.

## Prerequisites

- Python 3.7+
- pip
- Google Chrome

## Installation

### macOS / Linux

```bash
chmod +x install.sh
./install.sh
```

### Windows

```cmd
install.bat
```

The installer will:
1. Prompt you for your Chrome extension ID (find it at `chrome://extensions`)
2. Create the native messaging host manifest in the correct OS location
3. Install the `pynput` Python dependency

### macOS Accessibility Permission

On macOS, you must grant Accessibility permission to your terminal app (or Python) for keystroke simulation to work:

**System Preferences > Privacy & Security > Accessibility** — add your terminal app (Terminal, iTerm2, etc.).

## Usage

From a Chrome extension, send a message to the native host:

```javascript
chrome.runtime.sendNativeMessage(
  "com.propdream.keystroke_sender",
  { text: "Hello, world!" },
  (response) => {
    console.log(response);
    // { status: "ok", typed: 13 }
  }
);
```

### Message Format

**Request:**
```json
{
  "text": "string to type",
  "delay": 0.05
}
```

- `text` (required): The string to type as OS-level keystrokes.
- `delay` (optional): Seconds between each keystroke. Default: `0.05`.

**Response:**
```json
{ "status": "ok", "typed": 13 }
```

or on error:
```json
{ "status": "error", "message": "description" }
```

## Extension Setup

Add `"nativeMessaging"` to your extension's `manifest.json` permissions:

```json
{
  "permissions": ["nativeMessaging"]
}
```

## Uninstallation

### macOS / Linux

```bash
chmod +x uninstall.sh
./uninstall.sh
```

### Windows

```cmd
uninstall.bat
```

## Debugging

- Launch Chrome from the terminal to see native host stderr output
- Use `chrome://extensions` > Service Worker > Console to see extension-side errors
- Check `chrome.runtime.lastError` in the `sendNativeMessage` callback
