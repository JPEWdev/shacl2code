#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

SPDX3_MODEL = THIS_DIR / "data" / "spdx3-model.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "raw" / "spdx3.txt"


def test_generation_file(tmpdir):
    """
    Tests that shacl2code generates output to a file when requested
    """
    outfile = tmpdir.join("spdx3.txt")
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "raw",
            "--output",
            outfile,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_EXPECT.open("r") as f:
        assert outfile.read() == f.read()


def test_generation_stdout():
    """
    Tests that shacl2code generates output to stdout when requested
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "raw",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_generation_stdin():
    """
    Tests that shacl2code generates output from a model on stdin
    """
    with SPDX3_MODEL.open("r") as f:
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                "-",
                "raw",
                "--output",
                "-",
            ],
            check=True,
            stdin=f,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

    with SPDX3_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_generation_url(http_server):
    """
    Tests that shacl2code generates output from a model provided in a URL
    """
    shutil.copyfile(
        SPDX3_MODEL, os.path.join(http_server.document_root, "model.jsonld")
    )

    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            f"{http_server.uri}/model.jsonld",
            "raw",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_EXPECT.open("r") as f:
        assert p.stdout == f.read()
