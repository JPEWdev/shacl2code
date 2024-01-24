#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
import subprocess
import sys
from pathlib import Path

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

SPDX3_MODEL = THIS_DIR / "data" / "spdx3-model.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "python" / "spdx3.py"


def test_python_generation(tmpdir):
    """
    Tests that shacl2code generates python output that matches the expected
    output
    """
    outfile = tmpdir.join("spdx3.py")
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "python",
            "--output",
            outfile,
        ],
        check=True,
    )

    with SPDX3_EXPECT.open("r") as f:
        assert outfile.read() == f.read()


def test_output_syntax(tmpdir):
    """
    Checks that the output file is valid python syntax by executing it"
    """
    outfile = tmpdir.join("spdx3.py")
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "python",
            "--output",
            outfile,
        ],
        check=True,
    )

    subprocess.run([sys.executable, outfile, "--help"], check=True)


def test_trailing_whitespace():
    """
    Tests that the generated file does not have trailing whitespace
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "python",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    for num, line in enumerate(p.stdout.splitlines()):
        assert (
            re.search(r"\s+$", line) is None
        ), f"Line {num + 1} has trailing whitespace"


def test_tabs():
    """
    Tests that the output file doesn't contain tabs
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "python",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    for num, line in enumerate(p.stdout.splitlines()):
        assert "\t" not in line, f"Line {num + 1} has tabs"
