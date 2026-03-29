"""Compatibility launcher.

Single source of automation logic lives in springboard_engine.py.
This file is intentionally minimal to keep both entrypoints in sync.
"""

from springboard_engine import run_from_env


if __name__ == "__main__":
    run_from_env()
