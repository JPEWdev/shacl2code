#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import re
import subprocess
import json
import jsonschema
import pytest
from pathlib import Path

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"
EXPECT_DIR = THIS_DIR / "expect"

SPDX3_MODEL = DATA_DIR / "model" / "spdx3.jsonld"
SPDX3_EXPECT = THIS_DIR / "expect" / "jsonschema" / "spdx3.json"

SPDX3_CONTEXT = DATA_DIR / "model" / "spdx3-context.json"
SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"

SPDX3_CONTEXT_ARGS = ["--context-url", SPDX3_CONTEXT, SPDX3_CONTEXT_URL]


@pytest.mark.parametrize(
    "expect,args",
    [
        ("spdx3.json", []),
        ("spdx3-context.json", SPDX3_CONTEXT_ARGS),
    ],
)
class TestOutput:
    def test_generation(self, tmpdir, expect, args):
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

        with (EXPECT_DIR / "jsonschema" / expect).open("r") as f:
            assert outfile.read() == f.read()

    def test_output_syntax(self, expect, args):
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

    def test_trailing_whitespace(self, expect, args):
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

    def test_tabs(self, expect, args):
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


@pytest.mark.parametrize(
    "passes,file",
    [
        (True, "graph.json"),
        (True, "graph-empty.json"),
        (False, "graph-missing-context.json"),
        (False, "graph-unknown-root-field.json"),
        (False, "graph-unknown-field.json"),
        (False, "graph-unknown-field-nested.json"),
        (False, "graph-bad-context.json"),
        (True, "root.json"),
        (False, "root-missing-context.json"),
        (False, "root-bad-context.json"),
        (False, "root-unknown-field.json"),
        (False, "root-unknown-field-nested.json"),
        (False, "root-unknown-type.json"),
        (False, "context-only.json"),
        (True, "compact-array.json"),
    ],
)
def test_schema_validation(passes, file):
    with (EXPECT_DIR / "jsonschema" / "spdx3-context.json").open("r") as f:
        schema = json.load(f)

    with (DATA_DIR / "jsonschema" / file).open("r") as f:
        data = json.load(f)

    if passes:
        jsonschema.validate(data, schema=schema)
    else:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, schema=schema)
