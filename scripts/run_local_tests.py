#!/usr/bin/env python3
"""One-command offline-test runner for the owner's Windows VS Code workspace.

Only installs the public tzdata package if Windows has no IANA time-zone data.
Never reads credentials, live JRDB data or JRA services.
"""
import importlib
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]


def ensure_tokyo_timezone():
    try:
        ZoneInfo("Asia/Tokyo")
        return True
    except ZoneInfoNotFoundError:
        print(
            "Missing IANA time-zone data for Asia/Tokyo. Installing public tzdata once.",
            flush=True,
        )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "tzdata>=2025.2,<2027",
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        print(
            "Could not install tzdata. Check internet access and retry.",
            file=sys.stderr,
        )
        return False
    importlib.invalidate_caches()
    try:
        ZoneInfo("Asia/Tokyo")
    except ZoneInfoNotFoundError:
        print("Asia/Tokyo still unavailable. Restart VS Code and retry.", file=sys.stderr)
        return False
    return True


def main():
    if not ensure_tokyo_timezone():
        return 1
    print("ARC RACE: Running the local synthetic Python test suite.", flush=True)
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
    ]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
