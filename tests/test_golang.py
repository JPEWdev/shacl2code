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
import jsonvalidation

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

EXPECT_DIR = THIS_DIR / "expect"
DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


@pytest.fixture(scope="module")
def test_lib(tmp_path_factory, model_server):
    libdir = tmp_path_factory.mktemp("lib")
    model_source = libdir / "model.go"

    subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "--context",
            model_server + "/test-context.json",
            "golang",
            "--output",
            model_source,
        ],
        check=True,
    )

    subprocess.run(["go", "mod", "init", "model"], cwd=libdir, check=True)
    subprocess.run(["go", "mod", "tidy"], cwd=libdir, check=True)

    model_output = libdir / "model.a"

    subprocess.run(
        ["go", "build", "-o", model_output, "."],
        cwd=libdir,
        check=True,
    )

    return libdir


class Progress(Enum):
    COMPILE_FAILS = 0
    RUN_FAILS = 1
    VALIDATION_FAILS = 2
    RUNS = 3


@pytest.fixture
def compile_test(test_lib, tmp_path):
    def f(code_fragment, *, progress=Progress.RUNS, static=False, imports=[]):
        subprocess.run(
            ["go", "mod", "init", "test"],
            cwd=tmp_path,
            check=True,
        )

        subprocess.run(
            ["go", "mod", "edit", "-replace", f"model={test_lib}"],
            cwd=tmp_path,
            check=True,
        )

        src = tmp_path / "test.go"
        import_str = "\n".join(f'    "{i}"' for i in imports)
        src.write_text(
            textwrap.dedent(
                f"""\
                package main

                import (
                    "os"
                    "model"
                    "fmt"
                {import_str}
                )

                func test() error {{
                """
            )
            + textwrap.dedent(code_fragment)
            + textwrap.dedent(
                """\
                    return nil
                }

                func convertRefUnchecked[TO model.SHACLObject, FROM model.SHACLObject](in model.Ref[FROM]) model.Ref[TO] {
                    r, err := model.ConvertRef[TO, FROM](in)
                    if err != nil {
                        panic(err)
                    }
                    return r
                }


                func main() {
                    // This is necessary so that the model import doesn't
                    // generate an error
                    model.IsIRI("")
                    err := test()
                    if err == nil {
                        os.Exit(0)
                    }
                    switch err.(type) {
                    case *model.ValidationError:
                        fmt.Println("VALIDATION_FAILS", err)
                    default:
                        fmt.Println("ERROR", err)
                    }
                    os.Exit(1)
                }
                """
            )
        )
        subprocess.run(["go", "mod", "tidy"], cwd=tmp_path, check=True)

        prog = tmp_path / "prog"

        p = subprocess.run(
            ["go", "build", "-o", prog, "."],
            cwd=tmp_path,
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


@pytest.fixture(scope="module")
def validate_test(test_lib, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("validate")
    subprocess.run(
        ["go", "mod", "init", "validate"],
        cwd=tmp_path,
        check=True,
    )

    subprocess.run(
        ["go", "mod", "edit", "-replace", f"model={test_lib}"],
        cwd=tmp_path,
        check=True,
    )

    src = tmp_path / "validate.go"
    src.write_text(
        textwrap.dedent(
            """\
            package main

            import (
                "os"
                "model"
                "fmt"
                "encoding/json"
            )

            func main() {
                objset := model.NewSHACLObjectSet()

                file, err := os.Open(os.Args[1])
                if err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }
                defer file.Close()

                decoder := json.NewDecoder(file)

                if err := objset.Decode(decoder); err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }

                if ! objset.Validate(nil) {
                    fmt.Println("Validation failed")
                    os.Exit(1)
                }
                os.Exit(0)
            }
            """
        )
    )
    subprocess.run(["go", "mod", "tidy"], cwd=tmp_path, check=True)

    prog = tmp_path / "validate"

    subprocess.run(
        ["go", "build", "-o", prog, "."],
        cwd=tmp_path,
        check=True,
    )

    def f(path, passes):
        p = subprocess.run(
            [prog, path],
            encoding="utf-8",
        )
        if passes:
            assert p.returncode == 0, f"Validation failed when a pass was expected"
        else:
            assert p.returncode != 0, f"Validation passed when a failure was expected"

    yield f


@pytest.fixture(scope="module")
def roundtrip_test(test_lib, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("roundtrip")
    subprocess.run(
        ["go", "mod", "init", "roundtrip"],
        cwd=tmp_path,
        check=True,
    )

    subprocess.run(
        ["go", "mod", "edit", "-replace", f"model={test_lib}"],
        cwd=tmp_path,
        check=True,
    )

    src = tmp_path / "roundtrip.go"
    src.write_text(
        textwrap.dedent(
            """\
            package main

            import (
                "os"
                "model"
                "fmt"
                "encoding/json"
            )

            func main() {
                objset := model.NewSHACLObjectSet()

                in_file, err := os.Open(os.Args[1])
                if err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }
                defer in_file.Close()

                decoder := json.NewDecoder(in_file)

                if err := objset.Decode(decoder); err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }

                out_file, err := os.Create(os.Args[2])
                if err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }
                defer out_file.Close()

                encoder := json.NewEncoder(out_file)
                if err := objset.Encode(encoder); err != nil {
                    fmt.Println(err)
                    os.Exit(1)
                }
            }
            """
        )
    )
    subprocess.run(["go", "mod", "tidy"], cwd=tmp_path, check=True)

    prog = tmp_path / "roundtrip"

    subprocess.run(
        ["go", "build", "-o", prog, "."],
        cwd=tmp_path,
        check=True,
    )

    def f(in_path, out_path):
        subprocess.run(
            [prog, in_path, out_path],
            encoding="utf-8",
            check=True,
        )

    yield f


def test_trailing_whitespace():
    """
    Tests that the generated file does not have trailing whitespace
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "golang",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    for num, line in enumerate(p.stdout.splitlines()):
        assert (
            re.search(r"\s+$", line) is None
        ), f"Line {num + 1} has trailing whitespace"


def test_tabs():
    """
    Tests that the output file doesn't contain tabs
    """
    p = subprocess.run(
        [
            "shacl2code",
            "generate",
            "--input",
            TEST_MODEL,
            "golang",
            "--output",
            "-",
        ],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf-8",
    )

    for num, line in enumerate(p.stdout.splitlines()):
        assert "\t" not in line, f"Line {num + 1} has tabs"


def test_compile(compile_test):
    compile_test("")


GO_STRING = '"string"'


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        #
        # positive integer
        ("TestClassPositiveIntegerProp", "1", "1"),
        ("TestClassPositiveIntegerProp", "-1", Progress.VALIDATION_FAILS),
        ("TestClassPositiveIntegerProp", "0", Progress.VALIDATION_FAILS),
        # bool is converted to integer
        ("TestClassPositiveIntegerProp", "false", Progress.COMPILE_FAILS),
        ("TestClassPositiveIntegerProp", "true", Progress.COMPILE_FAILS),
        # Implicit conversion from double to int
        ("TestClassPositiveIntegerProp", "1.0", "1"),
        ("TestClassPositiveIntegerProp", "1.5", Progress.COMPILE_FAILS),
        ("TestClassPositiveIntegerProp", "-1.0", Progress.VALIDATION_FAILS),
        ("TestClassPositiveIntegerProp", "0.0", Progress.VALIDATION_FAILS),
        # String value
        ("TestClassPositiveIntegerProp", GO_STRING, Progress.COMPILE_FAILS),
        #
        # Non-negative integer
        ("TestClassNonnegativeIntegerProp", "1", "1"),
        ("TestClassNonnegativeIntegerProp", "-1", Progress.VALIDATION_FAILS),
        ("TestClassNonnegativeIntegerProp", "0", "0"),
        # bool is converted to integer
        ("TestClassNonnegativeIntegerProp", "false", Progress.COMPILE_FAILS),
        ("TestClassNonnegativeIntegerProp", "true", Progress.COMPILE_FAILS),
        # Implicit conversion from double to int
        ("TestClassNonnegativeIntegerProp", "1.0", "1"),
        ("TestClassNonnegativeIntegerProp", "1.5", Progress.COMPILE_FAILS),
        ("TestClassNonnegativeIntegerProp", "-1.0", Progress.VALIDATION_FAILS),
        ("TestClassNonnegativeIntegerProp", "0.0", "0"),
        # String value
        ("TestClassNonnegativeIntegerProp", GO_STRING, Progress.COMPILE_FAILS),
        #
        # Integer
        ("TestClassIntegerProp", "1", "1"),
        ("TestClassIntegerProp", "-1", "-1"),
        ("TestClassIntegerProp", "0", "0"),
        # bool is converted to integer
        ("TestClassIntegerProp", "false", Progress.COMPILE_FAILS),
        ("TestClassIntegerProp", "true", Progress.COMPILE_FAILS),
        # Implicit conversion from double to int
        ("TestClassIntegerProp", "1.0", "1"),
        ("TestClassIntegerProp", "1.5", Progress.COMPILE_FAILS),
        ("TestClassIntegerProp", "-1.0", "-1"),
        ("TestClassIntegerProp", "0.0", "0"),
        # String value
        ("TestClassIntegerProp", GO_STRING, Progress.COMPILE_FAILS),
        #
        # Float
        ("TestClassFloatProp", "-1", "-1"),
        ("TestClassFloatProp", "-1.0", "-1"),
        ("TestClassFloatProp", "0", "0"),
        ("TestClassFloatProp", "0.0", "0"),
        ("TestClassFloatProp", "1", "1"),
        ("TestClassFloatProp", "1.0", "1"),
        ("TestClassFloatProp", "false", Progress.COMPILE_FAILS),
        ("TestClassFloatProp", "true", Progress.COMPILE_FAILS),
        # String value
        ("TestClassFloatProp", GO_STRING, Progress.COMPILE_FAILS),
        #
        # Boolean prop
        ("TestClassBooleanProp", "true", "true"),
        ("TestClassBooleanProp", "1", Progress.COMPILE_FAILS),
        ("TestClassBooleanProp", "-1", Progress.COMPILE_FAILS),
        ("TestClassBooleanProp", "-1.0", Progress.COMPILE_FAILS),
        ("TestClassBooleanProp", "false", "false"),
        ("TestClassBooleanProp", "0", Progress.COMPILE_FAILS),
        ("TestClassBooleanProp", "0.0", Progress.COMPILE_FAILS),
        # String value
        ("TestClassBooleanProp", GO_STRING, Progress.COMPILE_FAILS),
        #
        # String Property
        ("TestClassStringScalarProp", GO_STRING, "string"),
        ("TestClassStringScalarProp", '""', ""),
        ("TestClassStringScalarProp", "0", Progress.COMPILE_FAILS),
        ("TestClassStringScalarProp", "1", Progress.COMPILE_FAILS),
        ("TestClassStringScalarProp", "1.0", Progress.COMPILE_FAILS),
        ("TestClassStringScalarProp", "0.0", Progress.COMPILE_FAILS),
        ("TestClassStringScalarProp", "true", Progress.COMPILE_FAILS),
        ("TestClassStringScalarProp", "false", Progress.COMPILE_FAILS),
        #
        # Enumerated value
        (
            "TestClassEnumProp",
            '"http://example.org/enumType/foo"',
            "http://example.org/enumType/foo",
        ),
        ("TestClassEnumProp", "model.EnumTypeFoo", "http://example.org/enumType/foo"),
        ("TestClassEnumProp", GO_STRING, Progress.VALIDATION_FAILS),
        ("TestClassEnumProp", "0", Progress.COMPILE_FAILS),
        ("TestClassEnumProp", "1", Progress.COMPILE_FAILS),
        ("TestClassEnumProp", "1.0", Progress.COMPILE_FAILS),
        ("TestClassEnumProp", "0.0", Progress.COMPILE_FAILS),
        ("TestClassEnumProp", "true", Progress.COMPILE_FAILS),
        ("TestClassEnumProp", "false", Progress.COMPILE_FAILS),
        #
        # Pattern validated string
        ("TestClassRegex", '"foo1"', "foo1"),
        ("TestClassRegex", '"foo2"', "foo2"),
        ("TestClassRegex", '"foo2a"', "foo2a"),
        ("TestClassRegex", '"bar"', Progress.VALIDATION_FAILS),
        ("TestClassRegex", '"fooa"', Progress.VALIDATION_FAILS),
        ("TestClassRegex", '"afoo1"', Progress.VALIDATION_FAILS),
        #
        # ID assignment
        ("ID", '"_:blank"', "_:blank"),
        ("ID", '"http://example.com/test"', "http://example.com/test"),
        ("ID", '"not-iri"', Progress.VALIDATION_FAILS),
        #
        ## Date Time
        # (
        #    "_test_class_datetimestamp_scalar_prop",
        #    "DateTime(0)",
        #    "1970-01-01T00:00:00Z",
        # ),
        # (
        #    "_test_class_datetimestamp_scalar_prop",
        #    "DateTime(12345,4800)",
        #    "1970-01-01T03:25:45+01:20",
        # ),
        # (
        #    "_test_class_datetimestamp_scalar_prop",
        #    "DateTime(12345,-4800)",
        #    "1970-01-01T03:25:45-01:20",
        # ),
        ## Implicit constructor not allowed
        # ("_test_class_datetimestamp_scalar_prop", "0", Progress.COMPILE_FAILS),
        # ("_test_class_datetimestamp_scalar_prop", "1.0", Progress.COMPILE_FAILS),
        # ("_test_class_datetimestamp_scalar_prop", C_STRING_VAL, Progress.COMPILE_FAILS),
        # (
        #    "_test_class_datetimestamp_scalar_prop",
        #    CPP_STRING_VAL,
        #    Progress.COMPILE_FAILS,
        # ),
    ],
)
def test_scalar_prop_validation(compile_test, prop, value, expect):
    output = compile_test(
        f"""\
        c := model.MakeTestClass()

        // Basic assignment
        err := c.{prop}().Set({value})
        if err != nil {{
            return err
        }}

        fmt.Println(c.{prop}().Get())
        return nil
        """,
        progress=expect if isinstance(expect, Progress) else Progress.RUNS,
    )

    if isinstance(expect, Progress):
        assert expect != Progress.RUNS
    else:
        expect_lines = [expect]
        output_lines = output.splitlines()
        assert (
            output_lines == expect_lines
        ), f"Invalid output. Expected {expect_lines!r}, got {output_lines!r}"


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # Blank node assignment
        (
            "TestClassClassProp",
            'model.MakeIRIRef[model.TestClass]("_:blank")',
            "IRI _:blank",
        ),
        (
            "TestClassClassProp",
            'model.MakeIRIRef[model.TestClass]("http://example.com/test")',
            "IRI http://example.com/test",
        ),
        # (
        #    "TestClassClassProp",
        #    'TestClassRef{}.SetIRI("not-iri")',
        #    Progress.VALIDATION_FAILS,
        # ),
        # Derived assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](d)",
            "OBJECT _:d",
        ),
        # Derived conversion
        (
            "TestClassClassProp",
            'convertRefUnchecked[model.TestClass](model.MakeIRIRef[model.TestDerivedClass]("_:blank"))',
            "IRI _:blank",
        ),
        # Parent assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](p)",
            Progress.COMPILE_FAILS,
        ),
        # Named individual assignment
        (
            "TestClassClassProp",
            "model.MakeIRIRef[model.TestClass](model.TestClassNamed)",
            "IRI http://example.org/test-class/named",
        ),
        ## Named individual, but wrong type
        # (
        #    "TestClassClassProp",
        #    "enumType::foo",
        #    Progress.VALIDATION_FAILS,
        # ),
        # Self assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](c)",
            "OBJECT _:c",
        ),
        # Self assignment (inferred generic)
        (
            "TestClassClassProp",
            "model.MakeObjectRef(c)",
            "OBJECT _:c",
        ),
        # Parent assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](p)",
            Progress.COMPILE_FAILS,
        ),
        #
        # Derived assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](d)",
            "OBJECT _:d",
        ),
        # Self assignment by string
        (
            "TestClassClassProp",
            "model.MakeIRIRef[model.TestClass](c.ID().Get())",
            "IRI _:c",
        ),
        # Non derived class assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](a)",
            Progress.COMPILE_FAILS,
        ),
    ],
)
def test_class_prop_validation(compile_test, prop, value, expect):
    output = compile_test(
        f"""\
        p := model.MakeParentClass()
        var err = p.ID().Set("_:p")
        if err != nil {{ return err }}

        d := model.MakeTestDerivedClass()
        err = d.ID().Set("_:d")
        if err != nil {{ return err }}

        c := model.MakeTestClass()
        err = c.ID().Set("_:c")
        if err != nil {{ return err }}

        a := model.MakeTestAnotherClass()
        err = a.ID().Set("_:a")
        if err != nil {{ return err }}

        v := {value}
        err = c.{prop}().Set(v)
        if err != nil {{ return err }}

        if c.{prop}().IsObj() {{
            fmt.Println("OBJECT", c.{prop}().GetObj().ID().Get())
        }} else {{
            fmt.Println("IRI", c.{prop}().GetIRI())
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


def test_roundtrip(tmp_path, roundtrip, roundtrip_test):
    out_file = tmp_path / "out.json"

    roundtrip_test(roundtrip, out_file)

    with roundtrip.open("r") as f:
        expect = json.load(f)

    with out_file.open("r") as f:
        actual = json.load(f)

    assert expect == actual


@jsonvalidation.validation_tests()
def test_json_validation(passes, data, tmp_path, test_context_url, validate_test):
    jsonvalidation.replace_context(data, test_context_url)

    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(data))

    validate_test(data_file, passes)


@jsonvalidation.type_tests()
def test_json_types(passes, data, tmp_path, test_context_url, validate_test):
    jsonvalidation.replace_context(data, test_context_url)

    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(data))

    validate_test(data_file, passes)
