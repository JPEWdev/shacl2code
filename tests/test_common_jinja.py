#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess
from pathlib import Path


THIS_DIR = Path(__file__).parent

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"
ABORT_TEMPLATE = THIS_DIR / "data" / "abort.j2"
BAD_ID_TEMPLATE = THIS_DIR / "data" / "bad-id.j2"


def test_jinja_abort(tmp_path):
    """
    Tests that an abort in Jinja causes generation to fail
    """
    outfile = tmp_path / "out.txt"
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "jinja",
            "--output",
            outfile,
            "--template",
            ABORT_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.returncode != 0, "Process exited successfully when a failure was expected"
    assert "Test abort" in p.stderr


def test_bad_id_get(tmp_path):
    """
    Tests that getting an ID that doesn't exists fails
    """
    outfile = tmp_path / "out.txt"
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "jinja",
            "--output",
            outfile,
            "--template",
            BAD_ID_TEMPLATE,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )

    assert p.returncode != 0, "Process exited successfully when a failure was expected"
    assert "KeyError" in p.stderr
