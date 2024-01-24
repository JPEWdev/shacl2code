#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import subprocess

from shacl2code.lang import LANGUAGES


def test_shacl2code_exists():
    """
    Tests that the shacl2code program exists
    """
    subprocess.run(["shacl2code", "--help"], check=True)


def test_lang_list():
    """
    Tests that the reported language list matches the actual language list
    """
    p = subprocess.run(
        ["shacl2code", "list", "--short"],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    assert sorted(p.stdout.splitlines()) == sorted(LANGUAGES.keys())
