# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2026 Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT

import importlib
import subprocess
import sys
from pathlib import Path

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


class TestModelAll:
    def test_wildcard_import_is_eager_and_matches_public_names(
        self, tmp_path: Path
    ) -> None:
        """``from mypkg import *`` yields the model's public names
        and requires loading the model.

        Generated without --context, so the domain class asserted below
        keeps its recognizable "http_..." varname.
        """
        module_name = "pymodel_star_check"
        output_dir = tmp_path / module_name
        shacl2code_generate(
            ["--input", TEST_MODEL],
            [],
            output_dir,
        )

        sys.path.insert(0, str(tmp_path))
        try:
            import sys as _sys

            before = set(_sys.modules)
            ns: dict = {}
            exec(f"from {module_name} import *", ns)
            imported = {k for k in ns if not k.startswith("__")}

            # Domain classes, from the test fixture model.
            assert "http_example_org_shacl2code_test_test_class" in imported
            assert "http_example_org_shacl2code_test_parent_class" in imported

            # Generator infrastructure: constants, base/encoder/decoder classes.
            assert "CONTEXT_URLS" in imported
            assert "SHACLObject" in imported
            assert "SHACLObjectSet" in imported
            assert "JSONLDDecoder" in imported
            assert "JSONLDEncoder" in imported
            # rdflib is a test dependency, so the RDF* classes are defined and
            # expected to be included.
            assert "RDFSerializer" in imported

            # Must not leak model.py's imports or internal bookkeeping state.
            assert not imported & {
                "TYPE_CHECKING",
                "Any",
                "List",
                "TypeVar",
                "json",
                "_ALL_NAMED_INDIVIDUAL_IDS",
                "_register_lock",
            }

            # The model was loaded as a side effect of the wildcard import.
            assert f"{module_name}.model" in (set(_sys.modules) - before)
        finally:
            sys.path.remove(str(tmp_path))
            for m in list(sys.modules):
                if m == module_name or m.startswith(module_name + "."):
                    del sys.modules[m]

    def test_protocols_submodule_import_stays_lazy(
        self, tmp_path: Path, test_context_url: str
    ) -> None:
        """Importing the ``protocols`` submodule must not load ``model``."""
        module_name = "pymodel_lazy_check"
        output_dir = tmp_path / module_name
        shacl2code_generate(
            ["--input", TEST_MODEL, "--context", test_context_url],
            ["--include-protocols", "yes"],
            output_dir,
        )

        sys.path.insert(0, str(tmp_path))
        try:
            import sys as _sys

            before = set(_sys.modules)
            importlib.import_module(f"{module_name}.protocols")
            assert f"{module_name}.model" not in (set(_sys.modules) - before)
        finally:
            sys.path.remove(str(tmp_path))
            for m in list(sys.modules):
                if m == module_name or m.startswith(module_name + "."):
                    del sys.modules[m]
