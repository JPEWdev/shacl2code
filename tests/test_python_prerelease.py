# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2026 Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT

import importlib
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"


def shacl2code_generate(args, python_args, outfile):
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
        ]
        + args
        + ["python"]
        + python_args
        + [
            "--output",
            outfile,
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    # Add a py.typed file for type checking
    (outfile / "py.typed").touch()
    return p


PRERELEASE_MODEL = DATA_DIR / "prerelease.ttl"


def test_is_prerelease_constant(tmp_path: Path) -> None:
    """IS_PRERELEASE reflects sh-to-code:isPreRelease without loading model.py."""
    prerelease_dir = tmp_path / "pymodel_prerelease"
    shacl2code_generate(["--input", PRERELEASE_MODEL], [], prerelease_dir)

    stable_dir = tmp_path / "pymodel_stable"
    shacl2code_generate(["--input", TEST_MODEL], [], stable_dir)

    assert "IS_PRERELEASE = True" in (prerelease_dir / "__init__.py").read_text()
    assert "IS_PRERELEASE = False" in (stable_dir / "__init__.py").read_text()

    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.warns(FutureWarning):
            pkg = importlib.import_module("pymodel_prerelease")
        assert pkg.IS_PRERELEASE is True
        # Reading the constant must not have loaded model.py.
        assert "pymodel_prerelease.model" not in sys.modules
    finally:
        sys.path.remove(str(tmp_path))
        for m in list(sys.modules):
            if m == "pymodel_prerelease" or m.startswith("pymodel_prerelease."):
                del sys.modules[m]


def test_prerelease_import_warning(tmp_path: Path) -> None:
    """Pre-release package warns FutureWarning on first import, any form; stable doesn't."""
    prerelease_dir = tmp_path / "pymodel_prerelease_import"
    shacl2code_generate(["--input", PRERELEASE_MODEL], [], prerelease_dir)

    stable_dir = tmp_path / "pymodel_stable_import"
    shacl2code_generate(["--input", TEST_MODEL], [], stable_dir)

    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.warns(FutureWarning):
            import pymodel_prerelease_import  # noqa: F401

        # Second import of an already-loaded module must not re-warn.
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            importlib.import_module("pymodel_prerelease_import")

        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            import pymodel_stable_import  # noqa: F401
    finally:
        sys.path.remove(str(tmp_path))
        for prefix in ("pymodel_prerelease_import", "pymodel_stable_import"):
            for m in list(sys.modules):
                if m == prefix or m.startswith(prefix + "."):
                    del sys.modules[m]
