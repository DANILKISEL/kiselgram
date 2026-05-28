#!/usr/bin/env python3
"""Standalone entry point for Kiselgram Video Server

Usage:
    python run_video_server.py              # port 5001, host 0.0.0.0
    python run_video_server.py 5002         # custom port
    python run_video_server.py 5002 127.0.0.1
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

if len(sys.argv) > 1:
    os.environ['VIDEO_PORT'] = sys.argv[1]
if len(sys.argv) > 2:
    os.environ['VIDEO_HOST'] = sys.argv[2]

from video_server.app import run
run()
