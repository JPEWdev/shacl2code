#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import os
import shutil
import subprocess
from pathlib import Path


THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

RAW_TEMPLATE = THIS_DIR / "data" / "raw.j2"
SPDX3_MODEL = THIS_DIR / "data" / "spdx3.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "raw" / "spdx3.txt"

CONTEXT_TEMPLATE = THIS_DIR / "data" / "context.j2"
SPDX3_CONTEXT = THIS_DIR / "data" / "spdx3-context.json"
SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"
SPDX3_CONTEXT_EXPECT = THIS_DIR / "expect" / "raw" / "spdx3-context.txt"


def test_generation_file(tmpdir):
    """
    Tests that shacl2code generates output to a file when requested
    """
    outfile = tmpdir.join("spdx3.txt")
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "jinja",
            "--output",
            outfile,
            "--template",
            RAW_TEMPLATE,
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
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
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
                "jinja",
                "--output",
                "-",
                "--template",
                RAW_TEMPLATE,
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
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_context_file():
    """
    Tests that a context file can be used from a file path
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "--context",
            SPDX3_CONTEXT,
            "--context-url",
            SPDX3_CONTEXT_URL,
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_CONTEXT_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_context_file_missing_url():
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "--context",
            SPDX3_CONTEXT,
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.returncode != 0, "Process exited successfully when an error was expected"


def test_context_url(http_server):
    shutil.copyfile(
        SPDX3_CONTEXT, os.path.join(http_server.document_root, "context.json")
    )

    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
            "--context",
            f"{http_server.uri}/context.json",
            "--context-url",
            SPDX3_CONTEXT_URL,
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_TEMPLATE,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    with SPDX3_CONTEXT_EXPECT.open("r") as f:
        assert p.stdout == f.read()
