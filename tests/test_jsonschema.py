#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
import subprocess
import json
import pytest
from pathlib import Path

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

SPDX3_MODEL = THIS_DIR / "data" / "spdx3.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "jsonschema" / "spdx3.json"

SPDX3_CONTEXT = THIS_DIR / "data" / "spdx3-context.json"
SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"

pytestmark = pytest.mark.parametrize(
    "expect,args",
    [
        (
            THIS_DIR / "expect" / "jsonschema" / "spdx3.json",
            [],
        ),
        (
            THIS_DIR / "expect" / "jsonschema" / "spdx3-context.json",
            ["--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL],
        ),
    ],
)


def test_generation(tmpdir, expect, args):
    """
    Tests that shacl2code generates json schema output that matches the
    expected output
    """
    outfile = tmpdir.join("spdx3.json")
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
        ]
        + args
        + [
            "jsonschema",
            "--output",
            outfile,
        ],
        check=True,
    )

    with expect.open("r") as f:
        assert outfile.read() == f.read()


def test_output_syntax(expect, args):
    """
    Checks that the output file is valid json syntax by parsing it with Python
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
        ]
        + args
        + [
            "jsonschema",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    json.loads(p.stdout)


def test_trailing_whitespace(expect, args):
    """
    Tests that the generated file does not have trailing whitespace
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
        ]
        + args
        + [
            "jsonschema",
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


def test_tabs(expect, args):
    """
    Tests that the output file doesn't contain tabs
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
        ]
        + args
        + [
            "jsonschema",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    for num, line in enumerate(p.stdout.splitlines()):
        assert "\t" not in line, f"Line {num + 1} has tabs"
