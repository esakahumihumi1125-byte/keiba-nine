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
            "Windows に Asia/Tokyo の時刻データがありません。"
            " 初回のみ tzdata をインストールします。",
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
            "tzdata をインストールできませんでした。"
            " インターネット接続を確認してください。",
            file=sys.stderr,
        )
        return False
    importlib.invalidate_caches()
    try:
        ZoneInfo("Asia/Tokyo")
    except ZoneInfoNotFoundError:
        print("Asia/Tokyo が見つかりません。VS Codeを再起動してください。", file=sys.stderr)
        return False
    return True


def main():
    if not ensure_tokyo_timezone():
        return 1
    print("ARC RACE: Python の合成テストを実行します。", flush=True)
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
