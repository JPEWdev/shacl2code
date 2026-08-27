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


@pytest.fixture(scope="module")
def prerelease_and_stable_modules(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a pre-release and a stable module once, shared by both tests below."""
    tmp_directory = tmp_path_factory.mktemp("prerelease")
    shacl2code_generate(
        ["--input", PRERELEASE_MODEL], [], tmp_directory / "pymodel_prerelease"
    )
    shacl2code_generate(["--input", TEST_MODEL], [], tmp_directory / "pymodel_stable")
    return tmp_directory


def test_is_prerelease_constant(prerelease_and_stable_modules: Path) -> None:
    """IS_PRERELEASE reflects sh-to-code:isPreRelease without loading model.py."""
    prerelease_dir = prerelease_and_stable_modules / "pymodel_prerelease"
    stable_dir = prerelease_and_stable_modules / "pymodel_stable"

    assert "IS_PRERELEASE = True" in (prerelease_dir / "__init__.py").read_text()
    assert "IS_PRERELEASE = False" in (stable_dir / "__init__.py").read_text()

    sys.path.insert(0, str(prerelease_and_stable_modules))
    try:
        with pytest.warns(FutureWarning):
            pkg = importlib.import_module("pymodel_prerelease")
        assert pkg.IS_PRERELEASE is True
        # Reading the constant must not have loaded model.py.
        assert "pymodel_prerelease.model" not in sys.modules
    finally:
        sys.path.remove(str(prerelease_and_stable_modules))
        for m in list(sys.modules):
            if m == "pymodel_prerelease" or m.startswith("pymodel_prerelease."):
                del sys.modules[m]


def test_prerelease_import_warning(prerelease_and_stable_modules: Path) -> None:
    """Pre-release package warns FutureWarning on first import, any form; stable doesn't."""
    sys.path.insert(0, str(prerelease_and_stable_modules))
    try:
        with pytest.warns(FutureWarning):
            import pymodel_prerelease  # noqa: F401

        # Second import of an already-loaded module must not re-warn.
        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            importlib.import_module("pymodel_prerelease")

        with warnings.catch_warnings():
            warnings.simplefilter("error", FutureWarning)
            import pymodel_stable  # noqa: F401
    finally:
        sys.path.remove(str(prerelease_and_stable_modules))
        for prefix in ("pymodel_prerelease", "pymodel_stable"):
            for m in list(sys.modules):
                if m == prefix or m.startswith(prefix + "."):
                    del sys.modules[m]
