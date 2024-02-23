#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import os
import shutil
import subprocess
import pytest
from pathlib import Path

import shacl2code


THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

RAW_TEMPLATE = THIS_DIR / "data" / "raw.j2"
SPDX3_MODEL = THIS_DIR / "data" / "model" / "spdx3.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "raw" / "spdx3.txt"
BAD_REFERENCE_MODEL = THIS_DIR / "data" / "bad-reference.jsonld"

CONTEXT_TEMPLATE = THIS_DIR / "data" / "context.j2"
CONTEXT_URL_TEMPLATE = THIS_DIR / "data" / "context-url.j2"
SPDX3_CONTEXT = THIS_DIR / "data" / "model" / "spdx3-context.json"
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
            "--context-url",
            SPDX3_CONTEXT,
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
            "--context-url",
            f"{http_server.uri}/context.json",
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


def test_context_args(http_server):
    shutil.copyfile(
        SPDX3_CONTEXT, os.path.join(http_server.document_root, "context.json")
    )
    shutil.copyfile(
        SPDX3_CONTEXT, os.path.join(http_server.document_root, "context2.json")
    )

    def do_test(*, contexts=[], url_contexts=[]):
        cmd = [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
        ]

        expect = []
        for c in contexts:
            cmd.extend(["--context", c])
            expect.append(c)

        for c, url in url_contexts:
            cmd.extend(["--context-url", c, url])
            expect.append(url)

        cmd += [
            "jinja",
            "--output",
            "-",
            "--template",
            CONTEXT_URL_TEMPLATE,
        ]

        p = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        assert p.stdout.splitlines() == expect

    # Single URL
    do_test(contexts=[f"{http_server.uri}/context.json"])

    # Multiple URLs
    do_test(
        contexts=[
            f"{http_server.uri}/context.json",
            f"{http_server.uri}/context2.json",
        ]
    )

    # URL rewriting
    do_test(
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
        ]
    )

    # Multiple URL rewriting
    do_test(
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
            (f"{http_server.uri}/context2.json", "http://foo/B.json"),
        ]
    )

    # Mixed
    do_test(
        contexts=[
            f"{http_server.uri}/context.json",
            f"{http_server.uri}/context2.json",
        ],
        url_contexts=[
            (f"{http_server.uri}/context.json", "http://foo/A.json"),
            (f"{http_server.uri}/context2.json", "http://foo/B.json"),
        ],
    )


def test_bad_model_class():
    with pytest.raises(shacl2code.ModelException):
        shacl2code.main(
            [
                "generate",
                "--input",
                str(BAD_REFERENCE_MODEL),
                "jinja",
                "--output",
                "-",
                "--template",
                str(CONTEXT_TEMPLATE),
            ]
        )
