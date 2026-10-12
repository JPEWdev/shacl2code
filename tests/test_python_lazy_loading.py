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
            ["--include-protocols", "iri"],
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

    def test_shacl_class_named_like_a_reserved_scaffolding_name(
        self, tmp_path: Path
    ) -> None:
        """A SHACL class named e.g. "TYPE_CHECKING" must not be shadowed by
        __init__.py's own scaffolding of the same name -- __getattr__ is
        only consulted when a real top-level name isn't found first, so
        varname() must rename the colliding class instead."""
        ttl_content = """
@base <http://example.org/shacl2code-test/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .

<http://example.org/shacl2code-test> a owl:Ontology ;
    rdfs:comment "A test ontology" ;
    rdfs:label "shacl2code-test" ;
    owl:versionInfo "1.0.0" .

<shadow-class> a sh:NodeShape, owl:Class ;
    rdfs:comment "Compact name collides with typing.TYPE_CHECKING" .
"""
        ttl_file = tmp_path / "shadow.ttl"
        ttl_file.write_text(ttl_content)

        context_content = """
{
  "@context": {
    "@base": "http://example.org/shacl2code-test/",
    "TYPE_CHECKING": "http://example.org/shacl2code-test/shadow-class"
  }
}
"""
        context_file = tmp_path / "shadow-context.json"
        context_file.write_text(context_content)

        module_name = "pymodel_reserved_name_shadow"
        output_dir = tmp_path / module_name
        shacl2code_generate(
            [
                "--input",
                str(ttl_file),
                "--context-url",
                str(context_file),
                "https://example.com/shadow-context.jsonld",
            ],
            [],
            output_dir,
        )

        sys.path.insert(0, str(tmp_path))
        try:
            m = importlib.import_module(module_name)

            # Real typing flag: unaffected.
            assert m.TYPE_CHECKING is False

            # Colliding class: renamed, not dropped.
            assert hasattr(m, "TYPE_CHECKING_")
            cls = m.TYPE_CHECKING_
            assert issubclass(cls, m.SHACLObject)
            assert cls().get_type() == "http://example.org/shacl2code-test/shadow-class"

            # `import *` exposes the renamed class, not the typing flag.
            ns: dict = {}
            exec(f"from {module_name} import *", ns)
            imported = {k for k in ns if not k.startswith("__")}
            assert "TYPE_CHECKING_" in imported
            assert "TYPE_CHECKING" not in imported

            # __init__.py's own scaffolding names must not leak, renamed or
            # not. vars(m), not dir(m): dir() also merges in model.py's
            # namespace, which legitimately has its own "Any" import.
            assert not (
                {"Any", "Callable", "Dict", "List", "TypeVar", "ModuleType"}
                & set(vars(m))
            )
        finally:
            sys.path.remove(str(tmp_path))
            for mod in list(sys.modules):
                if mod == module_name or mod.startswith(module_name + "."):
                    del sys.modules[mod]
