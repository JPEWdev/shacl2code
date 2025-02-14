#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import pytest
import re
import subprocess
import textwrap
import multiprocessing
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from testfixtures import jsonvalidation

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


@dataclass
class Lib:
    basename: str
    rpath: Path
    bindir: Path
    pkg_config: Path
    namespace: str
    directory: Path


def build_lib(tmp_path_factory, model_server, tmpname, *, namespace=None):
    tmp_directory = tmp_path_factory.mktemp(tmpname)
    basename = "model"
    out_basename = tmp_directory / basename
    install_dir = tmp_directory / "install"
    extra_args = []
    if namespace is not None:
        extra_args.extend(["--namespace", namespace])
    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context",
            model_server + "/test-context.json",
            "cpp",
            "--output",
            out_basename,
            "--version=0.0.1",
        ]
        + extra_args,
        check=True,
    )
    subprocess.run(
        [
            "make",
            "-j" + str(multiprocessing.cpu_count()),
            "CXXFLAGS=-Wall -Werror -g -save-temps",
        ],
        check=True,
        cwd=tmp_directory,
    )
    subprocess.run(
        ["make", "install", "PREFIX=" + str(install_dir)],
        check=True,
        cwd=tmp_directory,
    )
    pkg_config = tmp_directory / "pkg-config"
    pkg_config.write_text(
        textwrap.dedent(
            f"""\
            #! /bin/sh
            export PKG_CONFIG_PATH="{ str(install_dir / 'lib' / 'pkgconfig') }"
            exec pkg-config "$@"
            """
        )
    )
    pkg_config.chmod(0o755)

    return Lib(
        basename=basename,
        rpath=install_dir / "lib",
        bindir=install_dir / "bin",
        pkg_config=pkg_config,
        namespace=(
            re.sub(r"[^a-zA-Z0-9_]", "_", basename) if namespace is None else namespace
        ),
        directory=tmp_directory,
    )


@pytest.fixture(scope="module")
def test_lib(tmp_path_factory, model_server):
    yield build_lib(tmp_path_factory, model_server, "cpptestcontextsrc")


class Progress(Enum):
    COMPILE_FAILS = 0
    RUN_FAILS = 1
    VALIDATION_FAILS = 2
    CAST_FAILS = 3
    RUNS = 4


@pytest.fixture
def compile_test(test_lib, tmp_path):
    def f(code_fragment, *, progress=Progress.RUNS, static=False):
        src = tmp_path / "test.cpp"
        src.write_text(
            textwrap.dedent(
                f"""\
                #include "{test_lib.basename}/{test_lib.basename}.hpp"
                #include "{test_lib.basename}/{test_lib.basename}-jsonld.hpp"
                #include <iostream>
                #include <fstream>
                #include <iomanip>

                using namespace {test_lib.namespace};

                int main(int argc, char** argv) {{
                    try {{
                """
            )
            + textwrap.dedent(code_fragment)
            + "".join(
                textwrap.dedent(
                    f"""\
                    }} catch ({exc}& e) {{
                        std::cout << " {enum.name} " << e.what() << std::endl;
                        return 1;
                    """
                )
                for exc, enum in (
                    ("ValidationError", Progress.VALIDATION_FAILS),
                    ("std::bad_cast", Progress.CAST_FAILS),
                )
            )
            + textwrap.dedent(
                """\
                    }
                    return 0;
                }
                """
            )
        )

        prog = tmp_path / "prog"
        pkg_config_cmd = f"$({test_lib.pkg_config} --cflags --libs {test_lib.basename})"
        compile_cmd = [
            "g++",
            src,
            "-Wall",
            "-Werror",
            "-g",
            "-o",
            prog,
        ]

        if static:
            compile_cmd.extend(
                [
                    "-Wl,-Bstatic",
                    pkg_config_cmd,
                    "-Wl,-Bdynamic",
                ]
            )
        else:
            compile_cmd.extend(
                [
                    pkg_config_cmd,
                    f"-Wl,-rpath={test_lib.rpath}",
                ]
            )

        compile_script = tmp_path / "compile.sh"
        compile_script.write_text(
            textwrap.dedent(
                f"""\
                #! /bin/sh
                exec {" ".join(str(s) for s in compile_cmd)}
                """
            )
        )
        compile_script.chmod(0o755)

        p = subprocess.run(
            [compile_script],
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )
        if progress == Progress.COMPILE_FAILS:
            assert (
                p.returncode != 0
            ), f"Compile succeeded when failure was expected. Output: {p.stdout}"
            return None

        assert p.returncode == 0, f"Compile failed. Output: {p.stdout}"

        prog.chmod(0o755)

        p = subprocess.run(
            [prog],
            stdout=subprocess.PIPE,
            encoding="utf-8",
        )

        if progress == Progress.RUN_FAILS:
            assert (
                p.returncode != 0
            ), f"Run succeeded when failure was expected. Output: {p.stdout}"
            return None

        for e in Progress:
            if e == Progress.RUNS:
                continue

            if progress == e:
                assert (
                    p.returncode != 0
                ), f"Run succeeded when failure was expected. Output: {p.stdout}"

                assert (
                    e.name in p.stdout.rstrip()
                ), f"{e.name} was not raised in program. Output: {p.stdout}"
                return None

        assert p.returncode == 0, f"Run failed. Output: {p.stdout}"

        return p.stdout

    yield f


@pytest.mark.parametrize(
    "args,basename",
    [
        (
            ["--input", TEST_MODEL],
            "test",
        ),
        (
            ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
            "test-context",
        ),
    ],
)
class TestOutput:
    def test_trailing_whitespace(self, tmp_path, args, basename):
        """
        Tests that the generated file does not have trailing whitespace
        """
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "cpp",
                "--output",
                tmp_path / basename,
                "--version=0.0.1",
            ],
            check=True,
        )

        for fn in tmp_path.iterdir():
            with fn.open("r") as f:
                for lineno, line in enumerate(f.readlines()):
                    line = line.rstrip("\n")
                    assert (
                        re.search(r"\s+$", line) is None
                    ), f"{fn}: Line {lineno + 1} has trailing whitespace: {line!r}"

    def test_tabs(self, tmp_path, args, basename):
        """
        Tests that the output file doesn't contain tabs
        """
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "cpp",
                "--output",
                tmp_path / basename,
                "--version=0.0.1",
            ],
            check=True,
        )

        for fn in tmp_path.iterdir():
            if fn.name == "Makefile":
                continue

            with fn.open("r") as f:
                for lineno, line in enumerate(f.readlines()):
                    assert (
                        "\t" not in line
                    ), f"{fn}: Line {lineno + 1} has tabs: {line!r}"

    def test_output_compile(self, tmp_path, args, basename):
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "cpp",
                "--output",
                tmp_path / basename,
                "--version=0.0.1",
            ],
            check=True,
        )

        subprocess.run(
            [
                "make",
                "-j" + str(multiprocessing.cpu_count()),
                "CXXFLAGS=-Wall -Werror -g -save-temps",
            ],
            check=True,
            cwd=tmp_path,
        )

        install_dir = tmp_path / "install"
        subprocess.run(
            ["make", "install", "PREFIX=" + str(install_dir)],
            check=True,
            cwd=tmp_path,
        )


def test_compile(compile_test):
    compile_test("")


def test_headers(test_lib, tmp_path):
    for h in test_lib.directory.glob("*.hpp"):
        src = tmp_path / (h.name + ".cpp")
        src.write_text(
            textwrap.dedent(
                f"""\
                #include <{test_lib.basename}/{h.name}>

                int main(int argc, char** argv) {{
                    return 0;
                }}
                """
            )
        )

        prog = tmp_path / "prog"
        pkg_config_cmd = f"$({test_lib.pkg_config} --cflags --libs {test_lib.basename})"
        compile_cmd = [
            "g++",
            src,
            "-Wall",
            "-Werror",
            "-g",
            "-o",
            prog,
            pkg_config_cmd,
            f"-Wl,-rpath={test_lib.rpath}",
        ]

        compile_script = tmp_path / "compile.sh"
        compile_script.write_text(
            textwrap.dedent(
                f"""\
                #! /bin/sh
                exec {" ".join(str(s) for s in compile_cmd)}
                """
            )
        )
        compile_script.chmod(0o755)

        subprocess.run(
            [compile_script],
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )


def test_namespace(tmp_path_factory, model_server):
    build_lib(
        tmp_path_factory,
        model_server,
        "cppnamespace",
        namespace="foo::bar",
    )


def test_no_namespace(tmp_path_factory, model_server):
    build_lib(
        tmp_path_factory,
        model_server,
        "cppnamespace",
        namespace="",
    )


C_STRING_VAL = '"string"'
CPP_STRING_VAL = 'std::string("string")'


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        #
        # positive integer
        ("_test_class_positive_integer_prop", "1", "1"),
        ("_test_class_positive_integer_prop", "-1", Progress.VALIDATION_FAILS),
        ("_test_class_positive_integer_prop", "0", Progress.VALIDATION_FAILS),
        # bool is converted to integer
        ("_test_class_positive_integer_prop", "false", Progress.VALIDATION_FAILS),
        ("_test_class_positive_integer_prop", "true", "1"),
        # Implicit conversion from double to int
        ("_test_class_positive_integer_prop", "1.0", "1"),
        ("_test_class_positive_integer_prop", "1.5", "1"),
        ("_test_class_positive_integer_prop", "-1.0", Progress.VALIDATION_FAILS),
        ("_test_class_positive_integer_prop", "0.0", Progress.VALIDATION_FAILS),
        # String value
        ("_test_class_positive_integer_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        ("_test_class_positive_integer_prop", CPP_STRING_VAL, Progress.COMPILE_FAILS),
        #
        # Non-negative integer
        ("_test_class_nonnegative_integer_prop", "1", "1"),
        ("_test_class_nonnegative_integer_prop", "-1", Progress.VALIDATION_FAILS),
        ("_test_class_nonnegative_integer_prop", "0", "0"),
        # bool is converted to integer
        ("_test_class_nonnegative_integer_prop", "false", "0"),
        ("_test_class_nonnegative_integer_prop", "true", "1"),
        # Implicit conversion from double to int
        ("_test_class_nonnegative_integer_prop", "1.0", "1"),
        ("_test_class_nonnegative_integer_prop", "1.5", "1"),
        ("_test_class_nonnegative_integer_prop", "-1.0", Progress.VALIDATION_FAILS),
        ("_test_class_nonnegative_integer_prop", "0.0", "0"),
        # String value
        ("_test_class_nonnegative_integer_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        (
            "_test_class_nonnegative_integer_prop",
            CPP_STRING_VAL,
            Progress.COMPILE_FAILS,
        ),
        #
        # Integer
        ("_test_class_integer_prop", "1", "1"),
        ("_test_class_integer_prop", "-1", "-1"),
        ("_test_class_integer_prop", "0", "0"),
        # bool is converted to integer
        ("_test_class_integer_prop", "false", "0"),
        ("_test_class_integer_prop", "true", "1"),
        # Implicit conversion from double to int
        ("_test_class_integer_prop", "1.0", "1"),
        ("_test_class_integer_prop", "1.5", "1"),
        ("_test_class_integer_prop", "-1.0", "-1"),
        ("_test_class_integer_prop", "0.0", "0"),
        # String value
        ("_test_class_integer_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        ("_test_class_integer_prop", CPP_STRING_VAL, Progress.COMPILE_FAILS),
        #
        # Float
        ("_test_class_float_prop", "-1", "-1.0"),
        ("_test_class_float_prop", "-1.0", "-1.0"),
        ("_test_class_float_prop", "0", "0.0"),
        ("_test_class_float_prop", "0.0", "0.0"),
        ("_test_class_float_prop", "1", "1.0"),
        ("_test_class_float_prop", "1.0", "1.0"),
        ("_test_class_float_prop", "false", "0.0"),
        ("_test_class_float_prop", "true", "1.0"),
        # String value
        ("_test_class_float_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        ("_test_class_float_prop", CPP_STRING_VAL, Progress.COMPILE_FAILS),
        #
        # Boolean prop
        ("_test_class_boolean_prop", "true", "1"),
        ("_test_class_boolean_prop", "1", "1"),
        ("_test_class_boolean_prop", "-1", "1"),
        ("_test_class_boolean_prop", "-1.0", "1"),
        ("_test_class_boolean_prop", "false", "0"),
        ("_test_class_boolean_prop", "0", "0"),
        ("_test_class_boolean_prop", "0.0", "0"),
        # String value
        ("_test_class_boolean_prop", C_STRING_VAL, "1"),
        ("_test_class_boolean_prop", CPP_STRING_VAL, Progress.COMPILE_FAILS),
        #
        # String Property
        ("_test_class_string_scalar_prop", C_STRING_VAL, "string"),
        ("_test_class_string_scalar_prop", CPP_STRING_VAL, "string"),
        ("_test_class_string_scalar_prop", '""', ""),
        ("_test_class_string_scalar_prop", "0", Progress.RUN_FAILS),
        ("_test_class_string_scalar_prop", "1", Progress.COMPILE_FAILS),
        ("_test_class_string_scalar_prop", "1.0", Progress.COMPILE_FAILS),
        ("_test_class_string_scalar_prop", "0.0", Progress.COMPILE_FAILS),
        ("_test_class_string_scalar_prop", "true", Progress.COMPILE_FAILS),
        ("_test_class_string_scalar_prop", "false", Progress.COMPILE_FAILS),
        #
        # Enumerated value
        (
            "_test_class_enum_prop",
            '"http://example.org/enumType/foo"',
            "http://example.org/enumType/foo",
        ),
        (
            "_test_class_enum_prop",
            'std::string("http://example.org/enumType/foo")',
            "http://example.org/enumType/foo",
        ),
        ("_test_class_enum_prop", "enumType::foo", "http://example.org/enumType/foo"),
        ("_test_class_enum_prop", C_STRING_VAL, Progress.VALIDATION_FAILS),
        ("_test_class_enum_prop", CPP_STRING_VAL, Progress.VALIDATION_FAILS),
        ("_test_class_enum_prop", "0", Progress.RUN_FAILS),
        ("_test_class_enum_prop", "1", Progress.COMPILE_FAILS),
        ("_test_class_enum_prop", "1.0", Progress.COMPILE_FAILS),
        ("_test_class_enum_prop", "0.0", Progress.COMPILE_FAILS),
        ("_test_class_enum_prop", "true", Progress.COMPILE_FAILS),
        ("_test_class_enum_prop", "false", Progress.COMPILE_FAILS),
        #
        # Pattern validated string
        ("_test_class_regex", '"foo1"', "foo1"),
        ("_test_class_regex", '"foo2"', "foo2"),
        ("_test_class_regex", '"foo2a"', "foo2a"),
        ("_test_class_regex", '"bar"', Progress.VALIDATION_FAILS),
        ("_test_class_regex", '"fooa"', Progress.VALIDATION_FAILS),
        ("_test_class_regex", '"afoo1"', Progress.VALIDATION_FAILS),
        #
        # ID assignment
        ("_id", '"_:blank"', "_:blank"),
        ("_id", '"http://example.com/test"', "http://example.com/test"),
        ("_id", '"not-iri"', Progress.VALIDATION_FAILS),
        #
        # Date Time
        (
            "_test_class_datetimestamp_scalar_prop",
            "DateTime(0)",
            "1970-01-01T00:00:00Z",
        ),
        (
            "_test_class_datetimestamp_scalar_prop",
            "DateTime(12345,4800)",
            "1970-01-01T03:25:45+01:20",
        ),
        (
            "_test_class_datetimestamp_scalar_prop",
            "DateTime(12345,-4800)",
            "1970-01-01T03:25:45-01:20",
        ),
        # Implicit constructor not allowed
        ("_test_class_datetimestamp_scalar_prop", "0", Progress.COMPILE_FAILS),
        ("_test_class_datetimestamp_scalar_prop", "1.0", Progress.COMPILE_FAILS),
        ("_test_class_datetimestamp_scalar_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        (
            "_test_class_datetimestamp_scalar_prop",
            CPP_STRING_VAL,
            Progress.COMPILE_FAILS,
        ),
    ],
)
def test_scalar_prop_validation(compile_test, prop, value, expect):
    output = compile_test(
        f"""\
        // Set precision in case we output a floating point number
        std::cout << std::fixed << std::setprecision(1);

        auto c = make_obj<test_class>();

        // Basic assignment
        c->{prop} = {value};
        std::cout << c->{prop}.get() << std::endl;

        // Self assignment
        c->{prop} = c->{prop};
        std::cout << c->{prop}.get() << std::endl;

        // Copy assignment
        auto other = make_obj<test_class>();
        other->{prop} = c->{prop};
        std::cout << other->{prop}.get() << std::endl;
        """,
        progress=expect if isinstance(expect, Progress) else Progress.RUNS,
    )

    if isinstance(expect, Progress):
        assert expect != Progress.RUNS
    else:
        expect_lines = [expect] * 3
        output_lines = output.splitlines()
        assert (
            output_lines == expect_lines
        ), f"Invalid output. Expected {expect_lines!r}, got {output_lines!r}"


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # Blank node assignment
        ("_test_class_class_prop", 'Ref<test_class>("_:blank")', "IRI _:blank"),
        (
            "_test_class_class_prop",
            'Ref<test_class>("http://example.com/test")',
            "IRI http://example.com/test",
        ),
        (
            "_test_class_class_prop",
            'Ref<test_class>("not-iri")',
            Progress.VALIDATION_FAILS,
        ),
        # Derived assignment
        (
            "_test_class_class_prop",
            'Ref<test_derived_class>("_:blank")',
            "IRI _:blank",
        ),
        ("_test_class_class_prop", "d", "OBJECT _:d"),
        # Parent assignment
        (
            "_test_class_class_prop",
            'Ref<parent_class>("_:blank")',
            Progress.COMPILE_FAILS,
        ),
        # Named individual assignment
        (
            "_test_class_class_prop",
            "test_class::named",
            "IRI http://example.org/test-class/named",
        ),
        # Named individual, but wrong type
        (
            "_test_class_class_prop",
            "enumType::foo",
            Progress.VALIDATION_FAILS,
        ),
        ("_test_class_class_prop", "p", Progress.COMPILE_FAILS),
        # Self assignment
        ("_test_class_class_prop", "c", "OBJECT _:c"),
        # Self assignment by string
        ("_test_class_class_prop", "c->_id.get()", "IRI _:c"),
        # Non derived class assignment
        (
            "_test_class_class_prop",
            'Ref<test_another_class>("_:blank")',
            Progress.COMPILE_FAILS,
        ),
    ],
)
def test_class_prop_validation(compile_test, prop, value, expect):
    output = compile_test(
        f"""\
        auto p = make_obj<parent_class>();
        p->_id = "_:p";

        auto d = make_obj<test_derived_class>();
        d->_id = "_:d";

        auto c = make_obj<test_class>();
        c->_id = "_:c";

        c->{prop} = {value};
        if (c->{prop}.isObj()) {{
            std::cout << "OBJECT " << c->{prop}->_id.get() << std::endl;
        }} else {{
            std::cout << "IRI " << c->{prop}.iri() << std::endl;
        }}
        """,
        progress=expect if isinstance(expect, Progress) else Progress.RUNS,
    )

    if isinstance(expect, Progress):
        assert expect != Progress.RUNS
    else:
        assert (
            output.rstrip() == expect
        ), f"Bad output. Expected {expect!r}, got {output.rstrip()!r}"


@pytest.mark.parametrize(
    "A,B,progress",
    [
        # Cast to a parent class is allowed
        ("test_class", "parent_class", Progress.RUNS),
        # Cast to self is allowed
        ("test_class", "test_class", Progress.RUNS),
        # Cannot create referenced to a derived class from a parent cast
        ("test_class", "test_derived_class", Progress.COMPILE_FAILS),
        # Cannot create referenced to an unrelated class
        ("test_class", "test_another_class", Progress.COMPILE_FAILS),
    ],
)
def test_ref_implicit_cast(compile_test, A, B, progress):
    # Check types are valid
    compile_test(
        f"""\
        auto a = make_obj<{A}>();
        auto b = make_obj<{B}>();
        """
    )

    output = compile_test(
        f"""\
        auto a = make_obj<{A}>();
        a->_id = "_:foo";
        Ref<{B}> b(a);

        std::cout << b->_id.get() << std::endl;
        """,
        progress=progress,
    )
    if progress == Progress.RUNS:
        assert output.rstrip() == "_:foo"

    output = compile_test(
        f"""\
        auto a = make_obj<{A}>();
        a->_id = "_:foo";

        auto b = make_obj<{B}>();
        b = a;

        a.isObj();

        std::cout << b->_id.get() << std::endl;
        """,
        progress=progress,
    )
    if progress == Progress.RUNS:
        assert output.rstrip() == "_:foo"

    if progress == Progress.RUNS:
        output = compile_test(
            f"""\
            Ref<{A}> a("_:foo");
            Ref<{B}> b(a);

            std::cout << b.iri() << std::endl;
            """
        )
        assert output.rstrip() == "_:foo"

        output = compile_test(
            f"""\
            Ref<{A}> a("_:foo");
            Ref<{B}> b("_:bar");
            b = a;
            a.isObj();

            std::cout << b.iri() << std::endl;
            """
        )
        assert output.rstrip() == "_:foo"


def test_ref_prop_assignment(compile_test):
    output = compile_test(
        """\
        auto c = make_obj<test_class>();
        c->_test_class_class_prop = make_obj<test_class>();
        c->_test_class_class_prop->_id = "_:foo";

        auto d = make_obj<test_class>();
        d->_test_class_class_prop = c->_test_class_class_prop;

        std::cout << d->_test_class_class_prop->_id.get() << std::endl;
        """
    )

    assert output.rstrip() == "_:foo"


def test_ref_implicit_cast_to_abstract(compile_test):
    output = compile_test(
        """\
        auto r = make_obj<concrete_class>();
        r->_id = "_:foo";
        Ref<abstract_class> p(r);

        std::cout << p->_id.get() << std::endl;
        """
    )
    assert output.rstrip() == "_:foo"

    output = compile_test(
        """\
        Ref<concrete_class> a("_:foo");
        Ref<abstract_class> b(a);

        std::cout << b.iri() << std::endl;
        """
    )
    assert output.rstrip() == "_:foo"


@pytest.mark.parametrize(
    "A,B,progress",
    [
        # Explicit cast to parent class
        ("test_class", "parent_class", Progress.RUNS),
        # Explicit cast to self
        ("test_class", "test_class", Progress.RUNS),
        # Explicit cast to an unrelated object
        ("test_class", "test_another_class", Progress.COMPILE_FAILS),
    ],
)
def test_ref_explicit_cast(compile_test, A, B, progress):
    # Check types are valid
    compile_test(
        f"""\
        auto a = make_obj<{A}>();
        auto b = make_obj<{B}>();
        """
    )

    output = compile_test(
        f"""\
        auto a = make_obj<{A}>();
        a->_id = "_:foo";
        auto b = a.asTypeRef<{B}>();

        std::cout << b->_id.get() << std::endl;
        """,
        progress=progress,
    )
    if progress == Progress.RUNS:
        assert output.rstrip() == "_:foo"

    output = compile_test(
        f"""\
        auto a = make_obj<{A}>();
        a->_id = "_:foo";
        Ref<{B}> b = make_obj<{B}>();
        b = a.asTypeRef<{B}>();

        std::cout << b->_id.get() << std::endl;
        """,
        progress=progress,
    )
    if progress == Progress.RUNS:
        assert output.rstrip() == "_:foo"

    if progress == Progress.RUNS:
        output = compile_test(
            f"""\
            Ref<{A}> a("_:foo");
            auto b = a.asTypeRef<{B}>();
            std::cout << b.iri() << std::endl;
            """
        )
        assert output.rstrip() == "_:foo"

        output = compile_test(
            f"""\
            Ref<{A}> a("_:foo");
            Ref<{B}> b("bar");
            b = a.asTypeRef<{B}>();

            std::cout << b.iri() << std::endl;
            """
        )
        assert output.rstrip() == "_:foo"


def test_ref_explicit_cast_to_derived(compile_test):
    compile_test(
        """\
        auto r = make_obj<test_class>();
        auto p = r.asTypeRef<test_derived_class>();
        """,
        # Fails at runtime because r is not actually a test_derived_class
        progress=Progress.CAST_FAILS,
    )

    # Passes because it is a string reference
    output = compile_test(
        """\
        Ref<test_class> r("_:foo");
        auto p = r.asTypeRef<test_derived_class>();
        std::cout << p.iri() << std::endl;
        """
    )
    assert output.rstrip() == "_:foo"

    # Passes because r is actually a test_derived_class
    compile_test(
        """\
        auto r = make_obj<test_derived_class>();
        auto i = r.asTypeRef<parent_class>();
        auto p = i.asTypeRef<test_derived_class>();
        """
    )

    output = compile_test(
        """\
        Ref<test_derived_class> r("_:foo");
        auto i = r.asTypeRef<test_class>();
        auto p = i.asTypeRef<test_derived_class>();
        std::cout << p.iri() << std::endl;
        """
    )
    assert output.rstrip() == "_:foo"


def test_ref_explicit_cast_to_abstract(compile_test):
    output = compile_test(
        """\
        auto r = make_obj<concrete_class>();
        r->_id = "_:foo";
        auto p = r.asTypeRef<abstract_class>();

        std::cout << r->_id.get() << std::endl;
        """
    )
    assert output.rstrip() == "_:foo"


@pytest.mark.parametrize(
    "create_args,expect,tzoffset",
    [
        ((0,), "1970-01-01T00:00:00Z", 0),
        ((12345, 0), "1970-01-01T03:25:45Z", 0),
        ((12345, 3600), "1970-01-01T03:25:45+01:00", 3600),
        ((12345, 4800), "1970-01-01T03:25:45+01:20", 4800),
        ((12345, -3600), "1970-01-01T03:25:45-01:00", -3600),
        ((12345, -4800), "1970-01-01T03:25:45-01:20", -4800),
    ],
)
def test_DateTime_toString(compile_test, create_args, expect, tzoffset):
    args = ", ".join(repr(r) for r in create_args)
    output = compile_test(
        f"""\
        std::cout << DateTime({args}).toString() << std::endl;
        """
    )

    assert (
        output.rstrip() == expect
    ), f"Bad string result for DateTime({args}).toString(). Expected {expect!r}. Got {output.rstrip()!r}"

    output = compile_test(
        f"""\
        std::cout << DateTime({args}).tzOffsetSeconds() << std::endl;
        """
    )

    assert (
        int(output.rstrip()) == tzoffset
    ), f"Bad TZ offset. Expected {tzoffset!r}, got {int(output.rstrip())!r}"


@pytest.mark.parametrize(
    "s,valid,time,tzoffset",
    [
        ("1970-01-01T00:00:00Z", True, 0, 0),
        ("1970-01-01T03:25:45Z", True, 12345, 0),
        ("1970-01-01T03:25:45+00:00", True, 12345, 0),
        ("1970-01-01T03:25:45+01:00", True, 12345, 3600),
        ("1970-01-01T03:25:45+01:20", True, 12345, 4800),
        ("1970-01-01T03:25:45-01:00", True, 12345, -3600),
        ("1970-01-01T03:25:45-01:20", True, 12345, -4800),
        ("1970-01-01T03:25:45+01", False, 0, 0),
        ("1970-01-01T03:25:45-01", False, 0, 0),
        ("1970-01-01T03:25:45+1", False, 0, 0),
        ("1970-01-01T03:25:45-1", False, 0, 0),
        # Missing TimeZone
        ("1970-01-01T03:25:45", False, 0, 0),
        # Bad timezone hour
        ("1970-01-01T03:25:45-13:20", False, 0, 0),
        ("1970-01-01T03:25:45+13:20", False, 0, 0),
        # Bad timezone minute
        ("1970-01-01T03:25:45-10:-10", False, 0, 0),
        ("1970-01-01T03:25:45+10:60", False, 0, 0),
        ("1970-01-01T03:25:45-12:01", False, 0, 0),
        ("1970-01-01T03:25:45+12:01", False, 0, 0),
    ],
)
def test_DateTime_fromString(compile_test, s, valid, time, tzoffset):
    output = compile_test(
        f"""
        auto d = DateTime::fromString("{s}", true);
        if (d) {{
            auto dt = d.value();
            std::cout << dt.time() << std::endl;
            std::cout << dt.tzOffsetSeconds() << std::endl;
        }} else {{
            std::cout << "INVALID" << std::endl;
        }}
        """
    )

    if valid:
        expect = [str(time), str(tzoffset)]
    else:
        expect = ["INVALID"]
    actual = output.splitlines()
    assert actual == expect, f"Unexpected output. Got {actual!r}, expected {expect!r}"


def test_abstract_class(compile_test):
    compile_test(
        """\
        auto r = make_obj<abstract_class>();
        """,
        progress=Progress.COMPILE_FAILS,
    )


def test_id_alias(compile_test):
    output = compile_test(
        """\
        {
            auto c = make_obj<inherited_id_prop_class>();
            std::cout << c->_id.getIRI() << std::endl;

            auto p = c.asTypeRef<id_prop_class>();
            std::cout << p->_id.getIRI() << std::endl;

            auto b = c.asTypeRef<SHACLObject>();
            std::cout << b->_id.getIRI() << std::endl;
        }
        {
            auto c = make_obj<test_derived_class>();
            std::cout << c->_id.getIRI() << std::endl;

            auto p = c.asTypeRef<test_class>();
            std::cout << p->_id.getIRI() << std::endl;

            auto b = c.asTypeRef<SHACLObject>();
            std::cout << b->_id.getIRI() << std::endl;
        }
        """
    )
    expected = ["testid"] * 3 + ["@id"] * 3
    assert (
        output.splitlines() == expected
    ), f"Bad output. Expected {expected!r}, got {output.splitlines()!r}"


def test_mandatory_properties(compile_test, tmp_path):
    CODE = textwrap.dedent(
        """\
        auto c = make_obj<test_class_required>();
        c->_id = "_:blank";
        c->_test_class_required_string_scalar_prop = "foo";
        c->_test_class_required_string_list_prop.add("bar");
        c->_test_class_required_string_list_prop.add("baz");
        {code}

        SHACLObjectSet o;
        o.add(c);

        std::ofstream outfile;
        outfile.open("{fn}");

        JSONLDInlineSerializer s;
        s.write(outfile, o);
        outfile.close();
        """
    )

    # Verify that the base code works
    compile_test(CODE.format(code="", fn=tmp_path / "pass.json"))

    # Required scalar property
    compile_test(
        CODE.format(
            code="""\
            c->_test_class_required_string_scalar_prop.clear();
            """,
            fn=tmp_path / "fail.json",
        ),
        progress=Progress.VALIDATION_FAILS,
    )

    # Array that is cleared
    compile_test(
        CODE.format(
            code="""\
            c->_test_class_required_string_list_prop.clear();
            """,
            fn=tmp_path / "fail.json",
        ),
        progress=Progress.VALIDATION_FAILS,
    )

    # Array with too many items
    compile_test(
        CODE.format(
            code="""\
            c->_test_class_required_string_list_prop.add("too many");
            """,
            fn=tmp_path / "fail.json",
        ),
        progress=Progress.VALIDATION_FAILS,
    )


@pytest.fixture
def iterator_test(compile_test):
    def f(code, expect):
        output = compile_test(
            f"""\
            auto c = make_obj<test_class>();
            auto& p = c->_test_class_string_list_prop;
            {textwrap.dedent(code)}

            for (auto&& i : p) {{
                std::cout << i << std::endl;
            }}
            """
        )
        assert output.splitlines() == expect

    return f


class TestListIterators:
    def test_empty(self, iterator_test):
        # empty initializer
        iterator_test("", [])

    def test_push_back(self, iterator_test):
        iterator_test(
            """\
            p.push_back("A");
            p.push_back("B");
            p.push_back("C");
            """,
            ["A", "B", "C"],
        )

    def test_add(self, iterator_test):
        iterator_test(
            """\
            p.add("A");
            p.add("B");
            p.add("C");
            """,
            ["A", "B", "C"],
        )

    def test_insert(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), "A");
            p.insert(p.begin(), "B");
            p.insert(p.begin() + 2, "D");
            p.insert(p.end(), "C");
            p.insert(p.end() - 1, "E");
            """,
            ["B", "A", "D", "E", "C"],
        )

    def test_insert_initializer_list(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            p.insert(p.begin(), {"D", "E", "F"});
            p.insert(p.end(), {"H", "I", "J"});
            """,
            ["D", "E", "F", "A", "B", "C", "H", "I", "J"],
        )

    def test_clear(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            p.clear();
            """,
            [],
        )

    def test_erase_all(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            p.erase(p.begin(), p.end());
            """,
            [],
        )

    def test_erase_single(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            p.erase(p.begin() + 1);
            """,
            ["A", "C"],
        )

    def test_replace(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            *p.begin() = "D";
            *(p.begin() + 1) = "E";
            *(p.begin() + 2) = "F";
            """,
            ["D", "E", "F"],
        )

    def test_assign_std_initalizer_list(self, iterator_test):
        iterator_test(
            """\
            p = {"A", "B", "C"};
            p = {"D", "E", "F"};
            """,
            ["D", "E", "F"],
        )

    def test_assign_ListPropertyValue(self, iterator_test):
        iterator_test(
            """\
            auto d = make_obj<test_class>();
            d->_test_class_string_list_prop = {"A", "B", "C"};
            p = d->_test_class_string_list_prop;
            """,
            ["A", "B", "C"],
        )

    def test_assign_self(self, iterator_test):
        iterator_test(
            """\
            p = {"A", "B", "C"};
            p = p;
            """,
            ["A", "B", "C"],
        )

    def test_pointer(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            p.begin()->append("B");
            (p.begin() + 1)->append("C");
            """,
            ["AB", "BC", "C"],
        )

    def test_std_find(self, compile_test):
        output = compile_test(
            """\
            auto c = make_obj<test_class>();
            auto& p = c->_test_class_string_list_prop;

            p.insert(p.begin(), {"A", "B", "C"});
            auto it = std::find(p.begin(), p.end(), "A");
            std::cout << *it << std::endl;
            """
        )
        assert output.splitlines() + ["A"]

    def test_std_remove(self, iterator_test):
        # Yes this is actually how it works
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            auto it = std::remove(p.begin(), p.end(), "B");
            // std::remove() is [nodiscard]
            (void)it;
            """,
            ["A", "C", ""],
        )

        # std::remove() & erase() - For my own sanity :)
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "B", "C"});
            auto it = std::remove(p.begin(), p.end(), "B");
            p.erase(it, p.end());
            """,
            ["A", "C"],
        )

    def test_std_unique(self, iterator_test):
        # note only consecutive duplicates are erased
        iterator_test(
            """\
            p.insert(p.begin(), {"A", "A", "B", "B", "C", "A", "A"});
            p.erase(std::unique(p.begin(), p.end()), p.end());
            """,
            ["A", "B", "C", "A"],
        )

    def test_std_sort(self, iterator_test):
        iterator_test(
            """\
            p.insert(p.begin(), {"C", "B", "D", "A"});
            std::sort(p.begin(), p.end());
            """,
            ["A", "B", "C", "D"],
        )


def test_roundtrip(compile_test, tmp_path, roundtrip):
    out_file = tmp_path / "out.json"

    compile_test(
        f"""\
        SHACLObjectSet objs;
        {{
            std::ifstream infile;
            infile.open("{ roundtrip }");

            JSONLDDeserializer d;
            d.read(infile, objs);
            infile.close();
        }}
        {{
            std::ofstream outfile;
            outfile.open("{ out_file }");

            JSONLDInlineSerializer s;
            s.write(outfile, objs);
            outfile.close();
        }}
        """
    )

    with roundtrip.open("r") as f:
        expect = json.load(f)

    with out_file.open("r") as f:
        actual = json.load(f)

    assert expect == actual


def test_static(compile_test, tmp_path, roundtrip):
    out_file = tmp_path / "out.json"

    compile_test(
        f"""\
        SHACLObjectSet objs;
        {{
            std::ifstream infile;
            infile.open("{ roundtrip }");

            JSONLDDeserializer d;
            d.read(infile, objs);
            infile.close();
        }}
        {{
            std::ofstream outfile;
            outfile.open("{ out_file }");

            JSONLDInlineSerializer s;
            s.write(outfile, objs);
            outfile.close();
        }}
        """,
        static=True,
    )


def test_set(compile_test):
    output = compile_test(
        """
        auto c = make_obj<test_class>();
        c->set<&SHACLObject::_id>("_:foo").set<&test_class::_test_class_string_scalar_prop>("b");

        std::cout << c->_id.get() << std::endl;
        std::cout << c->_test_class_string_scalar_prop.get() << std::endl;
        """
    )

    assert output.splitlines() == ["_:foo", "b"]


def test_add(compile_test):
    output = compile_test(
        """
        auto c = make_obj<test_class>();
        c->add<&test_class::_test_class_string_list_prop>("a").add<&test_class::_test_class_string_list_prop>("b");

        for (auto const& i : c->_test_class_string_list_prop) {
            std::cout << i << std::endl;
        }

        """
    )

    assert output.splitlines() == ["a", "b"]


def test_docs(test_lib, tmp_path):
    FORCE_VALUES = {
        "WARN_AS_ERROR": "FAIL_ON_WARNINGS",
        "WARNINGS": "YES",
        "WARN_IF_UNDOCUMENTED": "YES",
        "WARN_IF_DOC_ERROR": "YES",
        "WARN_NO_PARAMDOC": "NO",
    }

    doxyfile = test_lib.directory / "Doxyfile"
    tmp_doxyfile = tmp_path / "Doxyfile"

    missing = set(FORCE_VALUES.keys())
    with doxyfile.open("r") as in_f, tmp_doxyfile.open("w") as out_f:
        for line in in_f.readlines():
            for k, v in FORCE_VALUES.items():
                if line.startswith(k):
                    out_f.write(f"{k} = {v}\n")
                    missing.remove(k)
                    break
            else:
                out_f.write(line)

    assert not missing, "Some Doxygen settings were not found: " + ", ".join(missing)

    subprocess.run(["doxygen", tmp_doxyfile], check=True, cwd=test_lib.directory)


@jsonvalidation.validation_tests()
def test_json_validation(passes, data, tmp_path, test_lib, test_context_url):
    jsonvalidation.replace_context(data, test_context_url)

    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(data))
    p = subprocess.run(
        [
            test_lib.bindir / f"{ test_lib.basename }-validate",
            data_file,
        ]
    )

    if passes:
        assert p.returncode == 0, "Validation failed when a pass was expected"
    else:
        assert p.returncode != 0, "Validation passed when failure was expected"


@jsonvalidation.type_tests()
def test_json_types(passes, data, tmp_path, test_lib, test_context_url):
    jsonvalidation.replace_context(data, test_context_url)

    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(data))
    p = subprocess.run(
        [
            test_lib.bindir / f"{ test_lib.basename }-validate",
            data_file,
        ]
    )

    if passes:
        assert p.returncode == 0, "Validation failed when a pass was expected"
    else:
        assert p.returncode != 0, "Validation passed when failure was expected"
