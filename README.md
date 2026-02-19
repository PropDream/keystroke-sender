# Keystroke Sender

A Chrome Native Messaging host that simulates OS-level keystrokes. Receives text strings from a Chrome extension and types them out as real key presses using `pynput`.

Works on **macOS**, **Linux**, and **Windows**.

Companion extension: [Chrome Form Filler](https://chromewebstore.google.com/detail/chrome-form-filler/dpdolkkncejkelemckjmjoaefmgdhepj) (`dpdolkkncejkelemckjmjoaefmgdhepj`)

## Prerequisites

- Python 3.7+
- pip
- Google Chrome
- [Chrome Form Filler](https://chromewebstore.google.com/detail/chrome-form-filler/dpdolkkncejkelemckjmjoaefmgdhepj) extension

## Installation

### pip install (recommended)

```bash
pip install git+https://github.com/PropDream/keystroke-sender.git
```

Then register the Chrome native messaging host:

```bash
keystroke-sender-register YOUR_EXTENSION_ID
```

To unregister later:

```bash
keystroke-sender-register --unregister
```

### Manual install (macOS / Linux)

```bash
chmod +x install.sh
./install.sh
```

### Manual install (Windows)

```cmd
install.bat
```

The manual installer will:
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

## Security

This app simulates real keystrokes and mouse clicks at the OS level, so it includes several safeguards to prevent misuse:

**Chrome Native Messaging isolation** — The host process can *only* be launched by Chrome, and *only* the extension ID you registered in `allowed_origins` can send it messages. No network socket is opened; communication is purely via stdin/stdout. An unauthorized extension or external program cannot talk to it.

**Idle timeout** — The host automatically exits after **1 minute** of inactivity. It does not stay running indefinitely.

**Rate limiting** — A maximum of **100 actions per second** is enforced. Bursts beyond this are rejected with an error response.

**Input size limits** — Messages larger than **1 MB** are rejected before parsing. Text payloads longer than **10,000 characters** are rejected before typing.

| Limit | Default |
|---|---|
| Idle timeout | 60 s (1 min) |
| Rate limit | 100 actions / 1 s |
| Max message size | 1 MB |
| Max text length | 10,000 chars |

These constants are defined at the top of `src/keystroke_sender/host.py` and can be adjusted if needed.

## Debugging

- Launch Chrome from the terminal to see native host stderr output
- Use `chrome://extensions` > Service Worker > Console to see extension-side errors
- Check `chrome.runtime.lastError` in the `sendNativeMessage` callback
