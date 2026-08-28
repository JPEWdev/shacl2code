# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2026 Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT
"""
Cross-version Protocol compatibility against the real SPDX 3 ontology.

The toy fixtures in test_python_protocols.py exercise the mechanism (a
class IRI that embeds a version segment, --include-protocols compact-name
vs. iri) in isolation. This file locks the same mechanism in against the
real, unmodified SPDX 3.0.1 and 3.1-dev models (168 classes, multiple
inheritance, enums, named individuals, and profiles like AI/Hardware)
vendored under tests/data/spdx/ -- see tests/data/spdx/README.md for
provenance and license. A future change to protocol_discriminator_name(),
prop_shape(), or the protocols.py.j2/model.py.j2 templates could pass every
toy-model test and still silently break compatibility against a real-world
ontology shaped like SPDX; these tests are what would catch that.

Coverage beyond the base classes (Element/CreationInfo/Tool/Relationship):
- Enum-typed properties (relationshipType, ai_autonomyType), whose values
  are NAMED_INDIVIDUALS-backed IRI constants, not raw strings -- a subtlety
  that only surfaces at runtime, not under mypy, since the property's
  static type is plain ``Optional[str]``.
- Named individuals as sentinel values (NoAssertionLicense/NoneLicense).
- A class from the AI profile (ai_AIPackage), not just Core.
- A class that exists ONLY in 3.1-dev (hardware_PhysicalHardware, from the
  Hardware profile) but subclasses a Core class present in 3.0.1
  (Artifact/Element) -- proving a 3.0.1-typed function accepts a type
  introduced by a later spec version it was never written against.
"""

import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union, get_type_hints

import pytest

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent
SPDX_DIR = THIS_DIR / "data" / "spdx"

SPDX301_DIR = SPDX_DIR / "3.0.1"
SPDX301_CONTEXT_URL = "https://spdx.org/rdf/3.0/spdx-context.jsonld"

SPDX31DEV_DIR = SPDX_DIR / "3.1-dev"
SPDX31DEV_CONTEXT_URL = "https://spdx.org/rdf/3.1/spdx-context.jsonld"

# The vendored .ttl/.jsonld files are excluded from the sdist (see
# pyproject.toml's [tool.hatch.build.targets.sdist] and
# tests/data/spdx/README.md's license note) -- they're only present in a
# git checkout. Skip gracefully rather than fail when they're absent.
pytestmark = pytest.mark.skipif(
    not (SPDX301_DIR / "spdx-model.ttl").exists()
    or not (SPDX31DEV_DIR / "spdx-model.ttl").exists(),
    reason=(
        "vendored SPDX fixture data not present (excluded from sdist; "
        "needs a full git checkout -- see tests/data/spdx/README.md)"
    ),
)


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


def _assert_typechecks_and_runs(script: Path, env: "dict[str, str]") -> None:
    """mypy --strict proves the *types* line up; actually running it proves
    construction succeeds too (e.g. enum properties validate against a
    fixed set of IRIs at runtime -- see PresenceType/RelationshipType's
    NAMED_INDIVIDUALS -- which mypy's Any-typed setters can't catch)."""
    r = subprocess.run(
        ["mypy", "--strict", str(script)],
        capture_output=True,
        encoding="utf-8",
        env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    r = subprocess.run(
        ["python", str(script)],
        capture_output=True,
        encoding="utf-8",
        env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def _generate_spdx(
    tmp_path_factory: pytest.TempPathFactory,
    name: str,
    model_dir: Path,
    context_url: str,
    pre_release: bool,
) -> Tuple[Path, str]:
    """Generate a --include-protocols compact-name module for one SPDX version.

    compact-name is required, not a stylistic choice: SPDX embeds its own
    spec version directly in every class/property IRI (e.g.
    https://spdx.org/rdf/3.0.1/terms/Core/CreationInfo vs.
    .../3.1/terms/Core/CreationInfo), so the 'iri' discriminator key would
    differ between 3.0.1 and 3.1-dev for every class -- see
    test_python_protocols.py::TestProtocolDiscriminatorKey for the same
    mechanism demonstrated on a minimal toy model.
    """
    outdir = tmp_path_factory.mktemp(name)
    module_name = f"spdx_{name}"
    args = [
        "--input",
        model_dir / "spdx-model.ttl",
        "--input",
        model_dir / "spdx-json-serialize-annotations.ttl",
        "--context-url",
        model_dir / "spdx-context.jsonld",
        context_url,
    ]
    if pre_release:
        args.append("--pre-release")
    shacl2code_generate(
        args,
        ["--include-protocols", "compact-name"],
        outdir / module_name,
    )
    return outdir, module_name


@pytest.fixture(scope="module")
def spdx301_pkg(tmp_path_factory: pytest.TempPathFactory) -> Tuple[Path, str]:
    """SPDX 3.0.1, generated once and shared by every test in this module."""
    return _generate_spdx(
        tmp_path_factory, "spdx301", SPDX301_DIR, SPDX301_CONTEXT_URL, False
    )


@pytest.fixture(scope="module")
def spdx31dev_pkg(tmp_path_factory: pytest.TempPathFactory) -> Tuple[Path, str]:
    """SPDX 3.1-dev (pre-release), generated once and shared."""
    return _generate_spdx(
        tmp_path_factory, "spdx31dev", SPDX31DEV_DIR, SPDX31DEV_CONTEXT_URL, True
    )


class TestSpdxProtocolSignature:
    """
    The generated protocols.py for a real, large ontology is well-formed
    Python and has the shape the codegen intends, at a scale (168 classes,
    multiple inheritance, named individuals) the smaller toy fixtures don't
    reach.
    """

    def test_flake8(self, spdx301_pkg: Tuple[Path, str]) -> None:
        module_path, module_name = spdx301_pkg
        r = subprocess.run(
            [
                "flake8",
                "--max-line-length=100",
                str(module_path / module_name / "protocols.py"),
            ],
            capture_output=True,
            encoding="utf-8",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_black(self, spdx301_pkg: Tuple[Path, str]) -> None:
        # Scoped to protocols.py, not the whole package: model.py/model.pyi
        # are unrelated to the Protocol feature and carry pre-existing,
        # local-black-version-only false-positive reformat hunks at
        # real-world scale (see tests/test_python_protocols.py's own
        # comments on this) that would make this test flaky for reasons
        # this file isn't meant to guard against.
        module_path, module_name = spdx301_pkg
        r = subprocess.run(
            ["black", "--check", str(module_path / module_name / "protocols.py")],
            capture_output=True,
            encoding="utf-8",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_expected_classes_and_shape(self, spdx301_pkg: Tuple[Path, str]) -> None:
        # Imports and inspects the actual runtime shape rather than
        # substring-matching generated source text, so this doesn't break
        # on a purely cosmetic codegen formatting change.
        module_path, module_name = spdx301_pkg
        sys.path.insert(0, str(module_path))
        try:
            protocols = importlib.import_module(f"{module_name}.protocols")

            # Base class with no properties of its own beyond the
            # discriminator.
            assert protocols.SHACLObjectProtocol in protocols.CreationInfo.__bases__
            # Single inheritance.
            assert protocols.Element in protocols.Relationship.__bases__
            assert protocols.Element in protocols.Tool.__bases__
            assert protocols.Element in protocols.Agent.__bases__
            # Multiple levels of inheritance.
            assert protocols.ElementCollection in protocols.SpdxDocument.__bases__
            assert protocols.Element in protocols.ElementCollection.__bases__

            # Object-reference properties precisely typed (not Any) for
            # reads. Discriminator keyed by compact name, matching the
            # class's own name.
            assert hasattr(protocols.CreationInfo, "_protocol_CreationInfo")
            assert hasattr(protocols.Element, "_protocol_Element")
            created_by_hints = get_type_hints(protocols.CreationInfo.createdBy.fget)
            assert created_by_hints["return"] == Iterable[Union[str, protocols.Agent]]

            # AI profile: a class from a non-Core profile, subclassing a
            # Software profile class, itself subclassing Core -- an enum
            # property (ai_autonomyType, a PresenceType).
            assert protocols.software_Package in protocols.ai_AIPackage.__bases__
            ai_hints = get_type_hints(protocols.ai_AIPackage)
            assert ai_hints["ai_autonomyType"] == Optional[str]

            # Named individuals: NoAssertionLicense/NoneLicense are
            # sentinel values (real IRIs, not synthetic test data) exposed
            # as class-level str constants via NAMED_INDIVIDUALS.
            individual_licensing_info = (
                protocols.expandedlicensing_IndividualLicensingInfo
            )
            assert (
                protocols.simplelicensing_AnyLicenseInfo
                in individual_licensing_info.__bases__
            )
            named_individual_hints = get_type_hints(individual_licensing_info)
            assert named_individual_hints["NoAssertionLicense"] == str
            assert named_individual_hints["NoneLicense"] == str
        finally:
            sys.path.remove(str(module_path))
            for m in list(sys.modules):
                if m == module_name or m.startswith(module_name + "."):
                    del sys.modules[m]

    def test_mypy_strict(self, spdx301_pkg: Tuple[Path, str]) -> None:
        module_path, module_name = spdx301_pkg
        env = _env_with_pythonpath(module_path)
        r = subprocess.run(
            ["mypy", "--strict", str(module_path / module_name / "protocols.py")],
            capture_output=True,
            encoding="utf-8",
            env=env,
        )
        assert r.returncode == 0, r.stdout + r.stderr


class TestSpdxCrossVersionProtocols:
    """
    Functions written once, typed against SPDX 3.0.1's Protocols, checked
    against both SPDX 3.0.1 and SPDX 3.1-dev objects -- and a class that is
    genuinely unrelated in the real model is still rejected. Mirrors the
    ad-hoc verification done manually against live-fetched SPDX models
    during development of this feature, now pinned as a regression test.

    Split by feature group (core/base classes vs. enum+named-individual+AI
    profile properties) rather than one large script, so a failure in one
    group doesn't bury the others in a single mypy/traceback dump.
    """

    def test_core_functions_accept_v301_and_v31dev_objects(
        self,
        tmp_path: Path,
        spdx301_pkg: Tuple[Path, str],
        spdx31dev_pkg: Tuple[Path, str],
    ) -> None:
        v301_path, v301_name = spdx301_pkg
        v31dev_path, v31dev_name = spdx31dev_pkg
        env = _env_with_pythonpath(v301_path, v31dev_path)

        script = tmp_path / "cross_version_accept_core.py"
        script.write_text(
            textwrap.dedent(f"""\
            from typing import Any, Iterable, Optional, Union
            import {v301_name}
            import {v31dev_name}
            from {v301_name} import protocols as p1

            # Functions written ONCE, typed against the OLDER (3.0.1)
            # Protocols -- never mentioning {v301_name} or {v31dev_name}
            # directly.

            def describe_creation_info(
                ci: p1.CreationInfo,
            ) -> Iterable[Union[str, p1.Agent]]:
                return ci.createdBy

            def summarize_element(e: p1.Element) -> Optional[str]:
                return e.name

            def relationship_targets(
                r: p1.Relationship,
            ) -> Iterable[Union[str, p1.Element]]:
                return r.to

            def tag_tool(t: p1.Tool, comment: str) -> None:
                t.comment = comment

            def set_creator(ci: p1.CreationInfo, agent: Any) -> None:
                ci.createdBy = [agent]

            # --- OLDER (3.0.1) objects ---
            older_ci = {v301_name}.CreationInfo(
                createdBy=[{v301_name}.Agent(spdxId="urn:older-agent")]
            )
            older_tool = {v301_name}.Tool(name="older-tool")
            older_agent = {v301_name}.Agent(spdxId="urn:older-set-creator-agent")
            older_rel = {v301_name}.Relationship(to=[older_tool])

            describe_creation_info(older_ci)
            summarize_element(older_tool)
            summarize_element(older_rel)
            relationship_targets(older_rel)
            tag_tool(older_tool, "hello")
            set_creator(older_ci, older_agent)

            # --- NEWER (3.1-dev) objects -- the actual cross-version proof:
            # these functions were never written against {v31dev_name} at
            # all, yet accept its objects.
            newer_ci = {v31dev_name}.CreationInfo(
                createdBy=[{v31dev_name}.Agent(spdxId="urn:newer-agent")]
            )
            newer_tool = {v31dev_name}.Tool(name="newer-tool")
            newer_agent = {v31dev_name}.Agent(spdxId="urn:newer-set-creator-agent")
            newer_rel = {v31dev_name}.Relationship(to=[newer_tool])

            describe_creation_info(newer_ci)
            summarize_element(newer_tool)
            summarize_element(newer_rel)
            relationship_targets(newer_rel)
            tag_tool(newer_tool, "hello from 3.1-dev")
            set_creator(newer_ci, newer_agent)
        """)
        )

        _assert_typechecks_and_runs(script, env)

    def test_enum_and_named_individual_properties_accept_v301_and_v31dev_objects(
        self,
        tmp_path: Path,
        spdx301_pkg: Tuple[Path, str],
        spdx31dev_pkg: Tuple[Path, str],
    ) -> None:
        """
        The properties/values that don't show up in the toy fixtures:
        enum-typed properties (relationshipType, ai_autonomyType) backed by
        NAMED_INDIVIDUALS IRI constants, a class from a non-Core profile
        (ai_AIPackage, from AI), and named-individual sentinel values
        (NoAssertionLicense/NoneLicense).
        """
        v301_path, v301_name = spdx301_pkg
        v31dev_path, v31dev_name = spdx31dev_pkg
        env = _env_with_pythonpath(v301_path, v31dev_path)

        script = tmp_path / "cross_version_accept_enums.py"
        script.write_text(
            textwrap.dedent(f"""\
            from typing import Optional, Union
            import {v301_name}
            import {v31dev_name}
            from {v301_name} import protocols as p1

            def relationship_type(r: p1.Relationship) -> Optional[str]:
                # Enum-typed property (RelationshipType named individuals).
                return r.relationshipType

            def summarize_ai_package(pkg: p1.ai_AIPackage) -> Optional[str]:
                # AI profile: subclasses Software profile's Package, which
                # subclasses Core's Artifact/Element.
                return pkg.name

            def ai_autonomy(pkg: p1.ai_AIPackage) -> Optional[str]:
                # Enum-typed property (PresenceType named individuals).
                return pkg.ai_autonomyType

            def license_or_id(
                value: Union[str, p1.expandedlicensing_IndividualLicensingInfo],
            ) -> str:
                # Named individuals: NoAssertionLicense/NoneLicense are
                # sentinel IRIs exposed as class-level str constants.
                return str(value)

            # --- OLDER (3.0.1) objects ---
            older_rel = {v301_name}.Relationship(
                to=[{v301_name}.Tool(name="older-target")],
                relationshipType={v301_name}.RelationshipType.describes,
            )
            older_ai_pkg = {v301_name}.ai_AIPackage(
                name="older-ai-pkg",
                ai_autonomyType={v301_name}.PresenceType.yes,
            )

            relationship_type(older_rel)
            summarize_ai_package(older_ai_pkg)
            ai_autonomy(older_ai_pkg)
            license_or_id(
                {v301_name}.expandedlicensing_IndividualLicensingInfo.NoAssertionLicense
            )

            # --- NEWER (3.1-dev) objects -- never written against
            # {v31dev_name} at all, yet accepted.
            newer_rel = {v31dev_name}.Relationship(
                to=[{v31dev_name}.Tool(name="newer-target")],
                relationshipType={v31dev_name}.RelationshipType.describes,
            )
            newer_ai_pkg = {v31dev_name}.ai_AIPackage(
                name="newer-ai-pkg",
                ai_autonomyType={v31dev_name}.PresenceType.noAssertion,
            )

            relationship_type(newer_rel)
            summarize_ai_package(newer_ai_pkg)
            ai_autonomy(newer_ai_pkg)
            license_or_id(
                {v31dev_name}.expandedlicensing_IndividualLicensingInfo.NoneLicense
            )
        """)
        )

        _assert_typechecks_and_runs(script, env)

    def test_v301_typed_functions_accept_v31dev_only_subclass(
        self,
        tmp_path: Path,
        spdx301_pkg: Tuple[Path, str],
        spdx31dev_pkg: Tuple[Path, str],
    ) -> None:
        """
        Future-proofing: a function typed against a 3.0.1 Protocol accepts
        an instance of a class that didn't exist when that Protocol was
        generated -- hardware_PhysicalHardware, from 3.1-dev's Hardware
        profile (absent from 3.0.1 entirely), whose ancestry
        (hardware_Hardware -> Artifact -> Element) reaches back to Core
        classes that DID exist in 3.0.1. Structural typing means the
        function only needs the ancestor's shape and discriminator, so any
        future subclass of an existing class -- from a profile that didn't
        exist yet, added by a later spec version -- satisfies it
        automatically, with no re-generation of the older side required.
        """
        v301_path, v301_name = spdx301_pkg
        v31dev_path, v31dev_name = spdx31dev_pkg
        env = _env_with_pythonpath(v301_path, v31dev_path)

        script = tmp_path / "future_proof.py"
        script.write_text(
            textwrap.dedent(f"""\
            from typing import Optional
            import {v301_name}
            import {v31dev_name}
            from {v301_name} import protocols as p1

            # Typed against 3.0.1's Artifact Protocol -- written before
            # the Hardware profile (3.1-only) existed.
            def artifact_summary(a: p1.Artifact) -> Optional[str]:
                return a.name

            hw = {v31dev_name}.hardware_PhysicalHardware(name="future-proof-hw")
            artifact_summary(hw)
        """)
        )

        _assert_typechecks_and_runs(script, env)

    def test_unrelated_class_rejected_by_protocol(
        self, tmp_path: Path, spdx301_pkg: Tuple[Path, str]
    ) -> None:
        module_path, module_name = spdx301_pkg
        env = _env_with_pythonpath(module_path)

        script = tmp_path / "cross_version_reject.py"
        script.write_text(
            textwrap.dedent(f"""\
            import {module_name}
            from {module_name} import protocols as p1

            def summarize_element(e: p1.Element) -> None:
                print(e.name)

            # CreationInfo does NOT inherit Element in the real SPDX model
            # -- must be rejected.
            bad = {module_name}.CreationInfo()
            summarize_element(bad)
        """)
        )

        r = subprocess.run(
            ["mypy", "--strict", str(script)],
            capture_output=True,
            encoding="utf-8",
            env=env,
        )
        assert r.returncode != 0, (
            "Expected mypy to reject CreationInfo as Element "
            "(they are unrelated in the real SPDX model)"
        )
        assert "incompatible type" in r.stdout
