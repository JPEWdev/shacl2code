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
TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"
TEST_EXPECT = THIS_DIR / "expect" / "raw" / "test.txt"


CONTEXT_TEMPLATE = THIS_DIR / "data" / "context.j2"
CONTEXT_URL_TEMPLATE = THIS_DIR / "data" / "context-url.j2"
TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"
TEST_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"
TEST_CONTEXT_EXPECT = THIS_DIR / "expect" / "raw" / "test-context.txt"


def test_generation_file(tmp_path):
    """
    Tests that shacl2code generates output to a file when requested
    """
    outfile = tmp_path / "out.txt"
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
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

    with TEST_EXPECT.open("r") as expect_f:
        with outfile.open("r") as out_f:
            assert out_f.read() == expect_f.read()


def test_generation_stdout():
    """
    Tests that shacl2code generates output to stdout when requested
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
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

    with TEST_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_generation_input_format(tmp_path):
    """
    Tests that shacl2code generates output correctly with an explicit input
    format
    """
    # File has no extension
    dest = tmp_path / "model"
    shutil.copy(TEST_MODEL, dest)

    # Passing the wrong input format should fail
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            dest,
            "--input-format",
            "json-ld",
            "jinja",
            "--output",
            "-",
            "--template",
            RAW_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )
    assert p.returncode != 0

    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            dest,
            "--input-format",
            "ttl",
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
    with TEST_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_generation_stdin():
    """
    Tests that shacl2code generates output from a model on stdin
    """
    with TEST_MODEL.open("r") as f:
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                "-",
                "--input-format",
                "ttl",
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

    with TEST_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_generation_stdin_auto_format():
    """
    Tests that shacl2code doesn't allow 'auto' format on stdin
    """
    with TEST_MODEL.open("r") as f:
        p = subprocess.run(
            [
                "shacl2code",
                "generate",
                "--input",
                "-",
                "--input-format",
                "auto",
                "jinja",
                "--output",
                "-",
                "--template",
                RAW_TEMPLATE,
            ],
            stdin=f,
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

    assert p.returncode != 0


def test_generation_url(model_server):
    """
    Tests that shacl2code generates output from a model provided in a URL
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            f"{model_server}/test.ttl",
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

    with TEST_EXPECT.open("r") as f:
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
            TEST_MODEL,
            "--context-url",
            TEST_CONTEXT,
            TEST_CONTEXT_URL,
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

    with TEST_CONTEXT_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_context_file_missing_url():
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context",
            TEST_CONTEXT,
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


def test_context_url(model_server):
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context-url",
            f"{model_server}/test-context.json",
            TEST_CONTEXT_URL,
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

    with TEST_CONTEXT_EXPECT.open("r") as f:
        assert p.stdout == f.read()


def test_context_args(http_server):
    shutil.copyfile(
        TEST_CONTEXT, os.path.join(http_server.document_root, "context.json")
    )
    shutil.copyfile(
        TEST_CONTEXT, os.path.join(http_server.document_root, "context2.json")
    )

    def do_test(*, contexts=[], url_contexts=[]):
        cmd = [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
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


@pytest.mark.parametrize(
    "file",
    [
        "bad-reference.jsonld",
        "missing-range.ttl",
        "bad-node-kind.ttl",
        "bad-pattern-class.ttl",
        "bad-pattern-integer.ttl",
    ],
)
def test_model_errors(file):
    with pytest.raises(shacl2code.ModelException):
        shacl2code.main(
            [
                "generate",
                "--input",
                str(THIS_DIR / "data" / file),
                "jinja",
                "--output",
                "-",
                "--template",
                str(CONTEXT_TEMPLATE),
            ]
        )
