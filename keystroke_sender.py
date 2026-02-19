#!/usr/bin/env python3
"""
Chrome Native Messaging host that simulates OS-level keystrokes.

Receives JSON messages from a Chrome extension via stdin and types
the specified text using pynput. Works on macOS, Linux, and Windows.

Message protocol: 4-byte uint32 length prefix (native byte order) + UTF-8 JSON.
Request:  {"text": "string to type"}
Response: {"status": "ok", "typed": <count>} or {"status": "error", "message": "..."}
"""

import sys
import os
import json
import struct
import time

# Ensure unbuffered stdout (critical for native messaging protocol)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(write_through=True)
os.environ["PYTHONUNBUFFERED"] = "1"


def log(text):
    """Write debug output to stderr (never stdout)."""
    sys.stderr.write(f"[keystroke-sender] {text}\n")
    sys.stderr.flush()


def read_message():
    """Read a single native messaging message from stdin."""
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        # Chrome disconnected
        sys.exit(0)
    if len(raw_length) < 4:
        log(f"Expected 4 bytes for length, got {len(raw_length)}")
        sys.exit(1)
    message_length = struct.unpack("@I", raw_length)[0]
    raw_message = sys.stdin.buffer.read(message_length)
    if len(raw_message) < message_length:
        log(f"Expected {message_length} bytes, got {len(raw_message)}")
        sys.exit(1)
    return json.loads(raw_message.decode("utf-8"))


def send_message(message_obj):
    """Send a single native messaging message to stdout."""
    encoded = json.dumps(message_obj, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def type_text(text, delay=0.05):
    """
    Simulate OS-level keystrokes for the given text using pynput.

    Args:
        text: The string to type.
        delay: Seconds to wait between each keystroke.

    Returns:
        The number of characters typed.
    """
    from pynput.keyboard import Controller

    keyboard = Controller()
    count = 0
    for char in text:
        keyboard.type(char)
        count += 1
        if delay > 0:
            time.sleep(delay)
    return count


def main():
    log("Native messaging host started")
    log(f"Platform: {sys.platform}")

    while True:
        try:
            message = read_message()
            log(f"Received: {message}")

            text = message.get("text")
            if text is None:
                send_message({"status": "error", "message": "Missing 'text' field"})
                continue

            if not isinstance(text, str):
                send_message({"status": "error", "message": "'text' must be a string"})
                continue

            if len(text) == 0:
                send_message({"status": "ok", "typed": 0})
                continue

            delay = message.get("delay", 0.05)
            typed = type_text(text, delay=delay)
            log(f"Typed {typed} characters")
            send_message({"status": "ok", "typed": typed})

        except json.JSONDecodeError as e:
            log(f"Invalid JSON: {e}")
            send_message({"status": "error", "message": f"Invalid JSON: {e}"})
        except Exception as e:
            log(f"Error: {e}")
            send_message({"status": "error", "message": str(e)})


if __name__ == "__main__":
    main()
