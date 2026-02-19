#!/usr/bin/env python3
"""
Chrome Native Messaging host that simulates OS-level keystrokes and mouse clicks.

Receives JSON messages from a Chrome extension via stdin and performs
OS-level input simulation using pynput. Works on macOS, Linux, and Windows.

Message protocol: 4-byte uint32 length prefix (native byte order) + UTF-8 JSON.

Actions:
  type:  {"action": "type", "text": "string to type", "delay": 0.05}
         -> {"status": "ok", "typed": <count>}
  click: {"action": "click", "x": 500, "y": 300}
         -> {"status": "ok", "action": "click", "x": 500, "y": 300}

Legacy (no action field): {"text": "..."} is treated as type action.
Error response: {"status": "error", "message": "..."}
"""

import sys
import os
import json
import struct
import threading
import time

# Ensure unbuffered stdout (critical for native messaging protocol)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(write_through=True)
os.environ["PYTHONUNBUFFERED"] = "1"

# --- Safety limits ---
MAX_MESSAGE_BYTES = 1_048_576  # 1 MB — reject anything larger
MAX_TEXT_LENGTH = 10_000       # max characters per type action
IDLE_TIMEOUT_SECONDS = 300     # exit after 5 min with no messages
RATE_LIMIT_WINDOW = 1.0        # rolling window in seconds
RATE_LIMIT_MAX = 20            # max actions per window


def log(text):
    """Write debug output to stderr (never stdout)."""
    sys.stderr.write(f"[keystroke-sender] {text}\n")
    sys.stderr.flush()


def read_message():
    """Read a single native messaging message from stdin.

    Raises ValueError if the message exceeds MAX_MESSAGE_BYTES.
    """
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        # Chrome disconnected
        sys.exit(0)
    if len(raw_length) < 4:
        log(f"Expected 4 bytes for length, got {len(raw_length)}")
        sys.exit(1)
    message_length = struct.unpack("@I", raw_length)[0]
    if message_length > MAX_MESSAGE_BYTES:
        log(f"Message too large: {message_length} bytes (limit {MAX_MESSAGE_BYTES})")
        raise ValueError(f"Message exceeds {MAX_MESSAGE_BYTES} byte limit")
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


def click_at(x, y):
    """
    Simulate an OS-level left mouse click at the given screen coordinates.

    Args:
        x: Screen X coordinate (pixels from left edge).
        y: Screen Y coordinate (pixels from top edge).
    """
    from pynput.mouse import Controller, Button

    mouse = Controller()
    mouse.position = (x, y)
    time.sleep(0.05)  # brief pause after moving to ensure position is set
    mouse.click(Button.left, 1)


def _check_rate_limit(timestamps):
    """Enforce a sliding-window rate limit. Returns True if the action is allowed."""
    now = time.monotonic()
    # Discard timestamps outside the window
    while timestamps and timestamps[0] <= now - RATE_LIMIT_WINDOW:
        timestamps.pop(0)
    if len(timestamps) >= RATE_LIMIT_MAX:
        return False
    timestamps.append(now)
    return True


def _start_idle_watchdog(last_activity_ref):
    """Background thread that exits the process after IDLE_TIMEOUT_SECONDS of inactivity."""
    def watchdog():
        while True:
            elapsed = time.monotonic() - last_activity_ref[0]
            remaining = IDLE_TIMEOUT_SECONDS - elapsed
            if remaining <= 0:
                log(f"Idle timeout ({IDLE_TIMEOUT_SECONDS}s) — exiting")
                os._exit(0)  # hard exit from background thread
            time.sleep(min(remaining, 10))
    t = threading.Thread(target=watchdog, daemon=True)
    t.start()


def main():
    log("Native messaging host started")
    log(f"Platform: {sys.platform}")
    log(f"Safety limits: idle_timeout={IDLE_TIMEOUT_SECONDS}s, "
        f"rate_limit={RATE_LIMIT_MAX}/{RATE_LIMIT_WINDOW}s, "
        f"max_text={MAX_TEXT_LENGTH}, max_msg={MAX_MESSAGE_BYTES}B")

    action_timestamps = []  # for rate limiting
    # Mutable ref so the watchdog thread can see updates
    last_activity = [time.monotonic()]
    _start_idle_watchdog(last_activity)

    while True:
        try:
            message = read_message()
        except ValueError as e:
            # Message size exceeded
            send_message({"status": "error", "message": str(e)})
            continue

        last_activity[0] = time.monotonic()

        try:
            log(f"Received: {message}")

            # --- Rate limit ---
            if not _check_rate_limit(action_timestamps):
                log("Rate limit exceeded")
                send_message({"status": "error", "message": f"Rate limit exceeded ({RATE_LIMIT_MAX} actions per {RATE_LIMIT_WINDOW}s)"})
                continue

            # Determine action: explicit "action" field, or default to "type" if "text" present
            action = message.get("action")
            if action is None:
                if "text" in message:
                    action = "type"
                else:
                    send_message({"status": "error", "message": "Missing 'action' field"})
                    continue

            if action == "type":
                text = message.get("text")
                if text is None:
                    send_message({"status": "error", "message": "Missing 'text' field"})
                    continue

                if not isinstance(text, str):
                    send_message({"status": "error", "message": "'text' must be a string"})
                    continue

                if len(text) > MAX_TEXT_LENGTH:
                    send_message({"status": "error", "message": f"Text too long ({len(text)} chars, limit {MAX_TEXT_LENGTH})"})
                    continue

                if len(text) == 0:
                    send_message({"status": "ok", "typed": 0})
                    continue

                delay = message.get("delay", 0.05)
                typed = type_text(text, delay=delay)
                log(f"Typed {typed} characters")
                send_message({"status": "ok", "typed": typed})

            elif action == "click":
                x = message.get("x")
                y = message.get("y")
                if x is None or y is None:
                    send_message({"status": "error", "message": "Missing 'x' or 'y' for click"})
                    continue

                x = int(x)
                y = int(y)
                click_at(x, y)
                log(f"Clicked at ({x}, {y})")
                send_message({"status": "ok", "action": "click", "x": x, "y": y})

            else:
                send_message({"status": "error", "message": f"Unknown action: {action}"})

        except json.JSONDecodeError as e:
            log(f"Invalid JSON: {e}")
            send_message({"status": "error", "message": f"Invalid JSON: {e}"})
        except Exception as e:
            log(f"Error: {e}")
            send_message({"status": "error", "message": str(e)})


if __name__ == "__main__":
    main()
