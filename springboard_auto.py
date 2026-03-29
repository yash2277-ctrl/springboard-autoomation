"""Compatibility launcher.

All automation logic is centralized in springboard_engine.py.
This file is kept only for backward compatibility.
"""

from springboard_engine import run_from_env


if __name__ == "__main__":
    run_from_env()
