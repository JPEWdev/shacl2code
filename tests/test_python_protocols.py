# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2026 Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT

import importlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable, Tuple

from jinja2 import TemplateRuntimeError

import pytest

import rdflib

from shacl2code.lang.python import protocols_use_datetime, protocols_use_object_refs
from shacl2code.model import Class, Model, Property
from shacl2code.urlcontext import UrlContext

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent
TOP_DIR = THIS_DIR.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

PRERELEASE_MODEL = DATA_DIR / "prerelease.ttl"


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


def _env_with_pythonpath(*paths: Path) -> "dict[str, str]":
    """A copy of the current environment with `paths` appended to PYTHONPATH."""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        env.get("PYTHONPATH", "").split(os.pathsep) + [str(p) for p in paths]
    )
    return env


TEST_V2_MODEL = THIS_DIR / "data" / "model" / "test-v2.ttl"
TEST_V3_MODEL = THIS_DIR / "data" / "model" / "test-v3.ttl"
TEST_V4_MODEL = THIS_DIR / "data" / "model" / "test-v4.ttl"
NO_DATETIME_MODEL = DATA_DIR / "no-datetime.ttl"


def _load_classes(ttl_path: Path) -> Iterable[Class]:
    """Parse a .ttl file in-process into Model.classes (no --context needed)."""
    graph = rdflib.Graph()
    graph.parse(ttl_path)
    return Model(graph, UrlContext()).classes


class TestProtocolsUseDatetime:
    """
    Direct, in-process unit tests for protocols_use_datetime(). Exercises both
    branches without going through code generation, so coverage doesn't depend
    on incidental property ordering in a generated model.
    """

    def test_true_when_datetime_property_present(self) -> None:
        """
        TEST_MODEL has scalar datetime properties (and list/enum/ref properties
        that sort before them), so this also exercises the "skip" continue
        branch on the way to the True return.
        """
        assert protocols_use_datetime(_load_classes(TEST_MODEL)) is True

    def test_false_when_no_datetime_property(self) -> None:
        """NO_DATETIME_MODEL has only a plain string property."""
        assert protocols_use_datetime(_load_classes(NO_DATETIME_MODEL)) is False

    def test_raises_on_unknown_datatype(self) -> None:
        """Unmapped datatype raises like model.py.j2's abort(), not KeyError."""
        bad_prop = Property(
            path="http://example.org/bad",
            varname="bad",
            datatype="http://example.org/not-a-real-datatype",
            max_count=1,
        )
        bad_class = Class(
            _id="http://example.org/BadClass",
            clsname="BadClass",
            parent_ids=[],
            derived_ids=[],
            properties=[bad_prop],
        )
        with pytest.raises(TemplateRuntimeError, match="Unknown data type"):
            protocols_use_datetime([bad_class])


class TestProtocolsUseObjectRefs:
    """
    Direct, in-process unit tests for protocols_use_object_refs(). Exercises
    both branches without going through code generation, so coverage doesn't
    depend on incidental property ordering in a generated model.
    """

    def test_true_when_object_ref_property_present(self) -> None:
        """TEST_MODEL has sh:class-typed scalar and list properties."""
        assert protocols_use_object_refs(_load_classes(TEST_MODEL)) is True

    def test_false_when_no_object_ref_property(self) -> None:
        """NO_DATETIME_MODEL has only a plain string property."""
        assert protocols_use_object_refs(_load_classes(NO_DATETIME_MODEL)) is False

    def test_false_for_enum_property(self) -> None:
        """
        An enum property also carries prop.class_id (pointing at the enum
        type), but prop_shape() excludes it from has_ref -- confirms
        protocols_use_object_refs() doesn't mistake an enum for an
        object-reference.
        """
        enum_prop = Property(
            path="http://example.org/color",
            varname="color",
            class_id="http://example.org/Color",
            enum_values=["red", "green"],
            max_count=1,
        )
        enum_only_class = Class(
            _id="http://example.org/EnumOnlyClass",
            clsname="EnumOnlyClass",
            parent_ids=[],
            derived_ids=[],
            properties=[enum_prop],
        )
        assert protocols_use_object_refs([enum_only_class]) is False


def _generate_protocols_fixture(
    tmp_path_factory: pytest.TempPathFactory,
    test_context_url: str,
    model_path: Path,
    version: str,
) -> Tuple[Path, str]:
    """Generate a --include-protocols iri module for one version fixture."""
    tmp_directory = tmp_path_factory.mktemp(f"protocols_{version}")
    module_name = f"pymodel_{version}"
    output_dir = tmp_directory / module_name
    shacl2code_generate(
        ["--input", model_path, "--context", test_context_url],
        ["--include-protocols", "iri"],
        output_dir,
    )
    (output_dir / "py.typed").touch()
    return tmp_directory, module_name


@pytest.fixture(scope="module")
def python_model_v1_protocols(
    tmp_path_factory: pytest.TempPathFactory, test_context_url: str
) -> Tuple[Path, str]:
    """v1 model generated with --include-protocols iri."""
    return _generate_protocols_fixture(
        tmp_path_factory, test_context_url, TEST_MODEL, "v1"
    )


@pytest.fixture(scope="module")
def python_model_v2_protocols(
    tmp_path_factory: pytest.TempPathFactory, test_context_url: str
) -> Tuple[Path, str]:
    """v2 model (backward-compatible extension) generated with --include-protocols iri."""
    return _generate_protocols_fixture(
        tmp_path_factory, test_context_url, TEST_V2_MODEL, "v2"
    )


@pytest.fixture(scope="module")
def python_model_v3_protocols(
    tmp_path_factory: pytest.TempPathFactory, test_context_url: str
) -> Tuple[Path, str]:
    """v3 model (backward-compatible extension of v2) with --include-protocols iri."""
    return _generate_protocols_fixture(
        tmp_path_factory, test_context_url, TEST_V3_MODEL, "v3"
    )


@pytest.fixture(scope="module")
def python_model_v4_protocols(
    tmp_path_factory: pytest.TempPathFactory, test_context_url: str
) -> Tuple[Path, str]:
    """v4 model (backward-compatible extension of v3) with --include-protocols iri."""
    return _generate_protocols_fixture(
        tmp_path_factory, test_context_url, TEST_V4_MODEL, "v4"
    )


@pytest.fixture(scope="module")
def python_model_no_datetime(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """--include-protocols iri generated from a model with no datetime property."""
    output_dir = tmp_path_factory.mktemp("no_datetime") / "pymodel"
    shacl2code_generate(
        ["--input", NO_DATETIME_MODEL],
        ["--include-protocols", "iri"],
        output_dir,
    )
    return output_dir


class TestProtocolOutput:
    """
    Tests for generated protocols.py - syntax, typing, and flake8.
    """

    def test_protocols_file_generated(
        self, python_model_v1_protocols: Tuple[Path, str]
    ) -> None:
        output_path, module_name = python_model_v1_protocols
        assert (output_path / module_name / "protocols.py").exists()

    def test_protocols_file_not_generated_by_default(
        self, tmp_path: Path, test_context_url: str
    ) -> None:
        output_dir = tmp_path / "pymodel"
        shacl2code_generate(
            ["--input", TEST_MODEL, "--context", test_context_url],
            [],
            output_dir,
        )
        assert not (output_dir / "protocols.py").exists()

    def test_dir_includes_lazy_names(
        self, python_model_v1_protocols: Tuple[Path, str]
    ) -> None:
        """
        __dir__() must expose model classes, "protocols", and "main" for
        dir()/tab-completion even though they are loaded lazily via
        __getattr__ (PEP 562).
        """
        output_path, module_name = python_model_v1_protocols

        sys.path.insert(0, str(output_path))
        try:
            pkg = importlib.import_module(module_name)
            names = dir(pkg)

            assert "test_class" in names
            assert "parent_class" in names
            assert "protocols" in names
            assert "main" in names

            # protocols.py is not itself lazily loaded, so dir() on the
            # lazy .protocols entry point must show its domain classes too --
            # confirms tab-completion works end to end through __getattr__.
            proto_names = dir(pkg.protocols)
            assert "SHACLObjectProtocol" in proto_names
            assert "test_class" in proto_names
        finally:
            sys.path.remove(str(output_path))
            for m in list(sys.modules):
                if m == module_name or m.startswith(module_name + "."):
                    del sys.modules[m]

    def test_mypy(self, python_model_v1_protocols: Tuple[Path, str]) -> None:
        output_path, module_name = python_model_v1_protocols
        subprocess.run(
            ["mypy", output_path / module_name], encoding="utf-8", check=True
        )

    def test_flake8_all_files(
        self, python_model_v1_protocols: Tuple[Path, str]
    ) -> None:
        """
        flake8 over the whole output directory with --include-protocols iri,
        not just protocols.py -- catches issues in the conditional protocols
        import inside __init__.py that a protocols.py-only check would miss.
        """
        output_path, module_name = python_model_v1_protocols
        output_dir = output_path / module_name
        subprocess.run(
            ["flake8", "--config", TOP_DIR / ".flake8"] + list(output_dir.iterdir()),
            encoding="utf-8",
            check=True,
        )

    def test_flake8_no_datetime_properties(
        self, python_model_no_datetime: Path
    ) -> None:
        """
        protocols.py must not unconditionally import `datetime` or `Union`.
        A model with no datetime-typed and no object-reference property must
        not produce an unused import (F401).
        """
        protocols_src = (python_model_no_datetime / "protocols.py").read_text()
        assert "import datetime" not in protocols_src
        assert "Union" not in protocols_src
        subprocess.run(
            [
                "flake8",
                "--config",
                TOP_DIR / ".flake8",
                python_model_no_datetime / "protocols.py",
            ],
            encoding="utf-8",
            check=True,
        )

    def test_mypy_no_datetime_properties(self, python_model_no_datetime: Path) -> None:
        """
        The generated package must still type-check when protocols.py omits
        the `datetime` import.
        """
        subprocess.run(["mypy", python_model_no_datetime], encoding="utf-8", check=True)


class TestProtocolConformance:
    """
    Type-checked usage tests: concrete classes satisfy their protocols,
    and the discriminator keeps structurally-identical classes distinct.
    """

    def test_conformance_mypy(
        self, python_model_v1_protocols: Tuple[Path, str], tmp_path: Path
    ) -> None:
        """
        Every concrete class must satisfy its generated Protocol under mypy strict.
        Verifies scalar read/write, object-ref typed read, Any-setter write.
        """
        module_path, module_name = python_model_v1_protocols
        env = _env_with_pythonpath(module_path)

        script = tmp_path / "conformance.py"
        script.write_text(textwrap.dedent(f"""\
            from typing import Any, Iterable, Optional, Union
            import {module_name}
            from {module_name} import protocols

            # Protocol conformance: assignment forces the static check.
            a: protocols.test_class = {module_name}.test_class()
            b: protocols.parent_class = {module_name}.parent_class()

            # Scalar read + write through protocol.
            def set_scalar(o: protocols.test_class, v: Optional[str]) -> None:
                o.test_class_string_scalar_prop = v

            # Object-ref typed read + Any-setter write through protocol.
            def get_ref(o: protocols.test_class) -> Optional[Union[str, protocols.test_class]]:
                return o.test_class_class_prop

            def get_ref_list(
                o: protocols.test_class,
            ) -> Iterable[Union[str, protocols.test_class]]:
                return o.test_class_class_list_prop

            def set_ref(o: protocols.test_class, v: {module_name}.test_class) -> None:
                o.test_class_class_prop = v

            # Version-agnostic function accepts any conforming class.
            def get_scalar(o: protocols.test_class) -> Optional[str]:
                result: Optional[str] = o.test_class_string_scalar_prop
                return result

            get_scalar(a)
        """))

        r = subprocess.run(
            ["mypy", "--strict", str(script)],
            encoding="utf-8",
            env=env,
            capture_output=True,
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_base_protocol_conformance_mypy(
        self, python_model_v1_protocols: Tuple[Path, str], tmp_path: Path
    ) -> None:
        """
        The hand-written SHACLObjectProtocol/SHACLObjectSetProtocol must be
        satisfied by the real generated SHACLObject/SHACLObjectSet, not just by
        per-class domain protocols. Guards against model.py.j2 changes to
        SHACLObject/SHACLObjectSet (e.g. renaming property_keys, retyping
        find_by_id's default, altering __contains__) silently breaking the
        base protocols with no test catching it.
        """
        module_path, module_name = python_model_v1_protocols
        env = _env_with_pythonpath(module_path)

        script = tmp_path / "base_conformance.py"
        script.write_text(textwrap.dedent(f"""\
            from typing import Iterable
            import {module_name}
            from {module_name} import protocols

            # Protocol conformance: assignment forces the static check.
            o: protocols.SHACLObjectProtocol = {module_name}.test_class()
            s: protocols.SHACLObjectSetProtocol = {module_name}.SHACLObjectSet()

            # Version-agnostic function accepts any conforming object/set.
            def get_id(obj: protocols.SHACLObjectProtocol) -> str:
                return obj.get_type()

            def iter_objects(
                objset: protocols.SHACLObjectSetProtocol,
            ) -> Iterable[protocols.SHACLObjectProtocol]:
                return objset.foreach()

            get_id(o)
            iter_objects(s)
        """))

        r = subprocess.run(
            ["mypy", "--strict", str(script)],
            encoding="utf-8",
            env=env,
            capture_output=True,
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_discriminator_mypy(
        self, python_model_v1_protocols: Tuple[Path, str], tmp_path: Path
    ) -> None:
        """
        The discriminator marker must prevent structurally-identical classes
        (test_class and another_class share no own properties in v1) from
        satisfying each other's protocol.
        """
        module_path, module_name = python_model_v1_protocols
        env = _env_with_pythonpath(module_path)

        # test_another_class has no own properties in v1, making it structurally
        # identical to test_class. Without the discriminator both would satisfy
        # each other's protocol.
        script = tmp_path / "discriminator.py"
        script.write_text(textwrap.dedent(f"""\
            import {module_name}
            from {module_name} import protocols

            bad: protocols.test_class = {module_name}.test_another_class()
        """))
        result = subprocess.run(
            ["mypy", "--strict", str(script)],
            encoding="utf-8",
            env=env,
            capture_output=True,
        )
        assert result.returncode != 0, (
            "Expected mypy to reject test_another_class as protocols.test_class "
            "(discriminator should prevent it)"
        )


class TestProtocolCrossVersion:
    """
    Cross-version: newer concrete classes must satisfy older-generated
    Protocols, and the discriminator still prevents wrong-type assignments
    across versions.

    Pairs cover chain-to-baseline (vN vs v1) plus adjacent (vN vs vN-1), so
    each new version is checked both against the original baseline and
    against the version it was directly derived from.
    """

    @pytest.mark.parametrize(
        "older_fixture,newer_fixture",
        [
            ("python_model_v1_protocols", "python_model_v2_protocols"),
            ("python_model_v1_protocols", "python_model_v3_protocols"),
            ("python_model_v2_protocols", "python_model_v3_protocols"),
            ("python_model_v1_protocols", "python_model_v4_protocols"),
            ("python_model_v3_protocols", "python_model_v4_protocols"),
        ],
    )
    def test_cross_version_mypy(
        self,
        older_fixture: str,
        newer_fixture: str,
        request: pytest.FixtureRequest,
        tmp_path: Path,
    ) -> None:
        """
        newer.test_class() satisfies older.protocols.test_class (backward-compat).
        newer.another_class() does NOT satisfy older.protocols.test_class
        (discriminator).
        """
        older_path, older_name = request.getfixturevalue(older_fixture)
        newer_path, newer_name = request.getfixturevalue(newer_fixture)
        env = _env_with_pythonpath(older_path, newer_path)

        script = tmp_path / "cross_version.py"
        script.write_text(textwrap.dedent(f"""\
            from typing import Iterable, Optional, Union
            import {older_name}, {newer_name}
            from {older_name} import protocols as op

            # newer concrete satisfies older Protocol (additive-only versions).
            a: op.test_class = {newer_name}.test_class()
            b: op.parent_class = {newer_name}.parent_class()

            # Scalar read through older protocol on newer object.
            def get_scalar(o: op.test_class) -> Optional[str]:
                result: Optional[str] = o.test_class_string_scalar_prop
                return result

            get_scalar(a)

            # Object-ref typed read through older protocol on newer object:
            # newer's own class_prop (typed with newer's own concrete class)
            # still satisfies older's precisely-typed Protocol getter.
            def get_ref(o: op.test_class) -> Optional[Union[str, op.test_class]]:
                return o.test_class_class_prop

            def get_ref_list(
                o: op.test_class,
            ) -> Iterable[Union[str, op.test_class]]:
                return o.test_class_class_list_prop

            # Any-setter write through older protocol on newer object.
            def set_ref(o: op.test_class, v: {newer_name}.test_class) -> None:
                o.test_class_class_prop = v

            # Discriminator: newer.another_class must NOT satisfy
            # older.protocols.test_class.
            bad: op.test_class = {newer_name}.test_another_class()  # type: ignore[assignment]
        """))

        subprocess.run(
            ["mypy", "--strict", str(script)],
            encoding="utf-8",
            env=env,
            check=True,
        )

        # Confirm the discriminator actually works (without the ignore).
        script2 = tmp_path / "cross_version_bad.py"
        script2.write_text(textwrap.dedent(f"""\
            import {older_name}, {newer_name}
            from {older_name} import protocols as op

            bad: op.test_class = {newer_name}.test_another_class()
        """))
        result = subprocess.run(
            ["mypy", "--strict", str(script2)],
            encoding="utf-8",
            env=env,
            capture_output=True,
        )
        assert result.returncode != 0, (
            "Expected mypy to reject newer.another_class as older.protocols.test_class "
            "across versions"
        )


def test_prerelease_with_protocols(tmp_path: Path) -> None:
    """
    --include-protocols and a pre-release model don't interact: the
    import-time warning still fires, and protocols.py is still generated
    and importable (protocols.py itself carries no pre-release awareness).
    """
    output_dir = tmp_path / "pymodel_prerelease_protocols"
    shacl2code_generate(
        ["--input", PRERELEASE_MODEL],
        ["--include-protocols", "iri"],
        output_dir,
    )
    assert "IS_PRERELEASE = True" in (output_dir / "__init__.py").read_text()
    assert (output_dir / "protocols.py").exists()

    sys.path.insert(0, str(tmp_path))
    try:
        with pytest.warns(FutureWarning):
            pkg = importlib.import_module("pymodel_prerelease_protocols")
        assert pkg.protocols is not None
    finally:
        sys.path.remove(str(tmp_path))
        for m in list(sys.modules):
            if m == "pymodel_prerelease_protocols" or m.startswith(
                "pymodel_prerelease_protocols."
            ):
                del sys.modules[m]


def _write_versioned_book_model(directory: Path, version: str) -> Tuple[Path, Path]:
    """A single-class toy model whose class IRI embeds `version`, mirroring
    SPDX's own practice of putting its spec version in every term IRI (e.g.
    https://spdx.org/rdf/3.0.1/terms/Core/CreationInfo vs .../3.1/terms/...).
    The compact term names ("Book", "title") stay the same across versions --
    only the context's target IRIs change -- mirroring SPDX's own context
    files (verified directly against spdx.org's 3.0.1 and 3.1 contexts).
    """
    base = f"http://example.org/toy/{version}"
    ttl = directory / f"book-{version}.ttl"
    ttl.write_text(f"""\
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<{base}/Book> a rdfs:Class, sh:NodeShape, owl:Class ;
    sh:property [
        sh:datatype xsd:string ;
        sh:path <{base}/Book/title> ;
        sh:maxCount 1
    ] .
""")
    context = directory / f"book-{version}-context.json"
    context.write_text(
        json.dumps(
            {
                "@context": {
                    "Book": f"{base}/Book",
                    "title": {"@id": f"{base}/Book/title"},
                }
            }
        )
    )
    return ttl, context


class TestProtocolDiscriminatorKey:
    """
    --include-protocols's discriminator key choice ("iri" vs
    "compact-name"), exercised against a toy model whose class IRI embeds a
    version segment -- the pattern SPDX itself uses. Existing fixtures
    (test.ttl/test-v2..v4.ttl) keep class IRIs stable across versions, so
    they can't exercise this.
    """

    @pytest.mark.parametrize(
        ("key", "expect_success"),
        [
            pytest.param(
                "compact-name",
                True,
                id="compact-name-survives",
            ),
            pytest.param(
                "iri",
                False,
                id="iri-breaks",
            ),
        ],
    )
    def test_discriminator_key_vs_versioned_class_iris(
        self, tmp_path: Path, key: str, expect_success: bool
    ) -> None:
        """
        'compact-name' keys the discriminator by the --context-compacted
        class name, which this toy model (like SPDX) keeps stable across
        versions even though the underlying class IRI changes -- so a newer
        Book still satisfies an older Book Protocol. 'iri' keys it by the
        class's full IRI, which this toy model changes between versions, so
        a newer Book does NOT satisfy an older Book Protocol -- proving the
        'compact-name' fix is real, not a no-op.
        """
        v1_ttl, v1_ctx = _write_versioned_book_model(tmp_path, "1.0.0")
        v2_ttl, v2_ctx = _write_versioned_book_model(tmp_path, "2.0.0")

        v1_dir = tmp_path / "book_v1"
        shacl2code_generate(
            [
                "--input",
                v1_ttl,
                "--context-url",
                v1_ctx,
                "http://example.org/toy/1.0.0/context.json",
            ],
            ["--include-protocols", key],
            v1_dir,
        )
        v2_dir = tmp_path / "book_v2"
        shacl2code_generate(
            [
                "--input",
                v2_ttl,
                "--context-url",
                v2_ctx,
                "http://example.org/toy/2.0.0/context.json",
            ],
            ["--include-protocols", key],
            v2_dir,
        )

        env = _env_with_pythonpath(v1_dir, v2_dir)
        script = tmp_path / "cross_version.py"
        script.write_text(textwrap.dedent("""\
            import book_v1, book_v2
            from book_v1 import protocols as p1

            b: p1.Book = book_v2.Book()
        """))
        if expect_success:
            subprocess.run(
                ["mypy", "--strict", str(script)],
                encoding="utf-8",
                env=env,
                check=True,
            )
        else:
            result = subprocess.run(
                ["mypy", "--strict", str(script)],
                encoding="utf-8",
                env=env,
                capture_output=True,
            )
            assert result.returncode != 0, (
                "Expected mypy to reject book_v2.Book as book_v1.protocols.Book "
                f"under the {key!r} discriminator key (versioned class IRIs)"
            )
