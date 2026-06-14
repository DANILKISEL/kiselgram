#!/usr/bin/env python3
"""Kiselgram Desktop — embedded webview wrapper for the K version."""
import sys

try:
    import webview
except ImportError:
    print("pywebview not found. Install with: pip3 install pywebview")
    sys.exit(1)

URL = sys.argv[1] if len(sys.argv) > 1 else "https://web.kiselgram.ru/k?view=desktop"

window = webview.create_window(
    title="Kiselgram Desktop",
    url=URL,
    width=1100,
    height=740,
    min_size=(400, 500),
    resizable=True,
    fullscreen=False,
    text_select=True,
    confirm_close=True,
)
webview.start(debug=False, http_server=False)
