#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess
from pathlib import Path


THIS_DIR = Path(__file__).parent

SPDX3_MODEL = THIS_DIR / "data" / "model" / "spdx3.jsonld"
ABORT_TEMPLATE = THIS_DIR / "data" / "abort.j2"
BAD_ID_TEMPLATE = THIS_DIR / "data" / "bad-id.j2"


def test_jinja_abort(tmpdir):
    """
    Tests that an abort in Jinja causes generation to fail
    """
    outfile = tmpdir.join("spdx3.txt")
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
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


def test_bad_id_get(tmpdir):
    """
    Tests that getting an ID that doens't exists fails
    """
    outfile = tmpdir.join("spdx3.txt")
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            SPDX3_MODEL,
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
