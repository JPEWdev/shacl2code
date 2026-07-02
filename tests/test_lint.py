#
# Copyright (c) 2026 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess
import sys
from pathlib import Path

import pytest

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent
TOP_DIR = THIS_DIR.parent


def test_black():
    if sys.version_info < (3, 10):
        pytest.skip("Black 26+ requires Python 3.10+")
    subprocess.run(["black", "--check", "."], cwd=TOP_DIR, check=True)


def test_flake8():
    files = subprocess.run(
        ["git", "ls-files", "*.py"],
        cwd=TOP_DIR,
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf",
    ).stdout.splitlines()

    subprocess.run(["flake8"] + files, cwd=TOP_DIR, check=True)
