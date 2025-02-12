#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import pytest
import re
import subprocess
import textwrap
import os
import os.path
from pathlib import Path
from enum import Enum
from testfixtures import jsonvalidation, timetests

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


@pytest.fixture(scope="module")
def test_lib(tmp_path_factory, model_server):
    libdir = tmp_path_factory.mktemp("lib")

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
            libdir,
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


def build_prog(test_lib, tmp_path_factory, name, code):
    tmp_path = tmp_path_factory.mktemp(name)
    subprocess.run(
        ["go", "mod", "init", name],
        cwd=tmp_path,
        check=True,
    )

    subprocess.run(
        ["go", "mod", "edit", "-replace", f"model={test_lib}"],
        cwd=tmp_path,
        check=True,
    )

    src = tmp_path / f"{name}.go"
    src.write_text(code)
    subprocess.run(["go", "mod", "tidy"], cwd=tmp_path, check=True)

    prog = tmp_path / name

    subprocess.run(
        ["go", "build", "-o", prog, "."],
        cwd=tmp_path,
        check=True,
    )

    def f(*args, **kwargs):
        subprocess.run(
            [prog] + list(args),
            encoding="utf-8",
            **kwargs,
        )

    return f


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
            assert p.returncode == 0, "Validation failed when a pass was expected"
        else:
            assert p.returncode != 0, "Validation passed when a failure was expected"

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


@pytest.fixture(scope="module")
def link_test(test_lib, tmp_path_factory):
    yield build_prog(
        test_lib,
        tmp_path_factory,
        "link",
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

                if ! objset.Validate(nil) {
                    fmt.Println("Validation failed")
                    os.Exit(1)
                }

                var expect model.SHACLObject = nil
                var check model.LinkClass = nil
                objset.Objects(func (o model.SHACLObject) bool {
                    c, ok := o.(model.LinkClass)
                    if !ok {
                        return true
                    }

                    if c.ID().IsSet() && c.ID().Get() == os.Args[2] {
                        check = c
                    }

                    if c.LinkClassTag().IsSet() && c.LinkClassTag().Get() == os.Args[3] {
                        expect = c
                    }

                    return true
                })

                if check == nil {
                    fmt.Println("Unable to find node", os.Args[2])
                    os.Exit(1)
                }

                if expect == nil {
                    fmt.Println("Unable to find tag", os.Args[3])
                    os.Exit(1)
                }

                checkObject := func (name string, r model.Ref[model.LinkClass]) {
                    if r == nil {
                        fmt.Println("Reference is nil for ", name)
                        os.Exit(1)
                    }

                    if !r.IsObj() {
                        fmt.Println("Reference in", name, "does not refer to an object")
                        if r.IsIRI() {
                            fmt.Println("Reference has IRI", r.GetIRI())
                        } else {
                            fmt.Println("Reference is empty")
                        }
                        os.Exit(1)
                    }

                    o := r.GetObj()

                    if o == nil {
                        fmt.Println("Object for", name, "is nil")
                        os.Exit(1)
                    }

                    if o != expect {
                        fmt.Println("Wrong object for", name, ". Got", o.ID().Get(), "expected", expect.ID().Get())
                        os.Exit(1)
                    }
                }

                checkObject("LinkClassLinkProp", check.LinkClassLinkProp().Get())
                checkObject("LinkClassLinkPropNoClass", check.LinkClassLinkPropNoClass().Get())
                checkObject("LinkClassLinkListProp[0]", check.LinkClassLinkListProp().Get()[0])
                checkObject("LinkClassLinkListProp[1]", check.LinkClassLinkListProp().Get()[1])
            }
            """
        ),
    )


@pytest.mark.parametrize(
    "args",
    [
        ["--input", TEST_MODEL],
        ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
    ],
)
class TestOutput:
    def test_trailing_whitespace(self, tmp_path, args):
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
                "golang",
                "--output",
                tmp_path,
            ],
            check=True,
        )

        for dirpath, dirnames, filenames in os.walk(tmp_path):
            for fn in filenames:
                with open(os.path.join(dirpath, fn)) as f:
                    for num, line in enumerate(f.read().splitlines()):
                        assert (
                            re.search(r"\s+$", line) is None
                        ), f"{fn}: Line {num + 1} has trailing whitespace: {line!r}"

    def test_tabs(self, tmp_path, args):
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
                "golang",
                "--output",
                tmp_path,
            ],
            check=True,
        )

        for dirpath, dirnames, filenames in os.walk(tmp_path):
            for fn in filenames:
                with open(os.path.join(dirpath, fn)) as f:
                    for num, line in enumerate(f.read().splitlines()):
                        assert (
                            "\t" not in line
                        ), f"{fn}: Line {num + 1} has tabs: {line!r}"

    def test_output_compile(self, tmp_path, args):
        subprocess.run(
            [
                "shacl2code",
                "generate",
            ]
            + args
            + [
                "golang",
                "--output",
                tmp_path,
            ],
            check=True,
        )

        subprocess.run(["go", "mod", "init", "model"], cwd=tmp_path, check=True)
        subprocess.run(["go", "mod", "tidy"], cwd=tmp_path, check=True)

        model_output = tmp_path / "model.a"

        subprocess.run(
            ["go", "build", "-o", model_output, "."],
            cwd=tmp_path,
            check=True,
        )


def test_compile(compile_test):
    compile_test("")


GO_STRING = '"string"'


@pytest.mark.parametrize(
    "prop,value,expect,imports",
    [
        #
        # positive integer
        ("TestClassPositiveIntegerProp", "1", "1", []),
        ("TestClassPositiveIntegerProp", "-1", Progress.VALIDATION_FAILS, []),
        ("TestClassPositiveIntegerProp", "0", Progress.VALIDATION_FAILS, []),
        # bool is converted to integer
        ("TestClassPositiveIntegerProp", "false", Progress.COMPILE_FAILS, []),
        ("TestClassPositiveIntegerProp", "true", Progress.COMPILE_FAILS, []),
        # Implicit conversion from double to int
        ("TestClassPositiveIntegerProp", "1.0", "1", []),
        ("TestClassPositiveIntegerProp", "1.5", Progress.COMPILE_FAILS, []),
        ("TestClassPositiveIntegerProp", "-1.0", Progress.VALIDATION_FAILS, []),
        ("TestClassPositiveIntegerProp", "0.0", Progress.VALIDATION_FAILS, []),
        # String value
        ("TestClassPositiveIntegerProp", GO_STRING, Progress.COMPILE_FAILS, []),
        #
        # Non-negative integer
        ("TestClassNonnegativeIntegerProp", "1", "1", []),
        ("TestClassNonnegativeIntegerProp", "-1", Progress.VALIDATION_FAILS, []),
        ("TestClassNonnegativeIntegerProp", "0", "0", []),
        # bool is converted to integer
        ("TestClassNonnegativeIntegerProp", "false", Progress.COMPILE_FAILS, []),
        ("TestClassNonnegativeIntegerProp", "true", Progress.COMPILE_FAILS, []),
        # Implicit conversion from double to int
        ("TestClassNonnegativeIntegerProp", "1.0", "1", []),
        ("TestClassNonnegativeIntegerProp", "1.5", Progress.COMPILE_FAILS, []),
        ("TestClassNonnegativeIntegerProp", "-1.0", Progress.VALIDATION_FAILS, []),
        ("TestClassNonnegativeIntegerProp", "0.0", "0", []),
        # String value
        ("TestClassNonnegativeIntegerProp", GO_STRING, Progress.COMPILE_FAILS, []),
        #
        # Integer
        ("TestClassIntegerProp", "1", "1", []),
        ("TestClassIntegerProp", "-1", "-1", []),
        ("TestClassIntegerProp", "0", "0", []),
        # bool is converted to integer
        ("TestClassIntegerProp", "false", Progress.COMPILE_FAILS, []),
        ("TestClassIntegerProp", "true", Progress.COMPILE_FAILS, []),
        # Implicit conversion from double to int
        ("TestClassIntegerProp", "1.0", "1", []),
        ("TestClassIntegerProp", "1.5", Progress.COMPILE_FAILS, []),
        ("TestClassIntegerProp", "-1.0", "-1", []),
        ("TestClassIntegerProp", "0.0", "0", []),
        # String value
        ("TestClassIntegerProp", GO_STRING, Progress.COMPILE_FAILS, []),
        #
        # Float
        ("TestClassFloatProp", "-1", "-1", []),
        ("TestClassFloatProp", "-1.0", "-1", []),
        ("TestClassFloatProp", "0", "0", []),
        ("TestClassFloatProp", "0.0", "0", []),
        ("TestClassFloatProp", "1", "1", []),
        ("TestClassFloatProp", "1.0", "1", []),
        ("TestClassFloatProp", "false", Progress.COMPILE_FAILS, []),
        ("TestClassFloatProp", "true", Progress.COMPILE_FAILS, []),
        # String value
        ("TestClassFloatProp", GO_STRING, Progress.COMPILE_FAILS, []),
        #
        # Boolean prop
        ("TestClassBooleanProp", "true", "true", []),
        ("TestClassBooleanProp", "1", Progress.COMPILE_FAILS, []),
        ("TestClassBooleanProp", "-1", Progress.COMPILE_FAILS, []),
        ("TestClassBooleanProp", "-1.0", Progress.COMPILE_FAILS, []),
        ("TestClassBooleanProp", "false", "false", []),
        ("TestClassBooleanProp", "0", Progress.COMPILE_FAILS, []),
        ("TestClassBooleanProp", "0.0", Progress.COMPILE_FAILS, []),
        # String value
        ("TestClassBooleanProp", GO_STRING, Progress.COMPILE_FAILS, []),
        #
        # String Property
        ("TestClassStringScalarProp", GO_STRING, "string", []),
        ("TestClassStringScalarProp", '""', "", []),
        ("TestClassStringScalarProp", "0", Progress.COMPILE_FAILS, []),
        ("TestClassStringScalarProp", "1", Progress.COMPILE_FAILS, []),
        ("TestClassStringScalarProp", "1.0", Progress.COMPILE_FAILS, []),
        ("TestClassStringScalarProp", "0.0", Progress.COMPILE_FAILS, []),
        ("TestClassStringScalarProp", "true", Progress.COMPILE_FAILS, []),
        ("TestClassStringScalarProp", "false", Progress.COMPILE_FAILS, []),
        #
        # Enumerated value
        (
            "TestClassEnumProp",
            '"http://example.org/enumType/foo"',
            "http://example.org/enumType/foo",
            [],
        ),
        (
            "TestClassEnumProp",
            "model.EnumTypeFoo",
            "http://example.org/enumType/foo",
            [],
        ),
        ("TestClassEnumProp", GO_STRING, Progress.VALIDATION_FAILS, []),
        ("TestClassEnumProp", "0", Progress.COMPILE_FAILS, []),
        ("TestClassEnumProp", "1", Progress.COMPILE_FAILS, []),
        ("TestClassEnumProp", "1.0", Progress.COMPILE_FAILS, []),
        ("TestClassEnumProp", "0.0", Progress.COMPILE_FAILS, []),
        ("TestClassEnumProp", "true", Progress.COMPILE_FAILS, []),
        ("TestClassEnumProp", "false", Progress.COMPILE_FAILS, []),
        #
        # Pattern validated string
        ("TestClassRegex", '"foo1"', "foo1", []),
        ("TestClassRegex", '"foo2"', "foo2", []),
        ("TestClassRegex", '"foo2a"', "foo2a", []),
        ("TestClassRegex", '"bar"', Progress.VALIDATION_FAILS, []),
        ("TestClassRegex", '"fooa"', Progress.VALIDATION_FAILS, []),
        ("TestClassRegex", '"afoo1"', Progress.VALIDATION_FAILS, []),
        #
        # ID assignment
        ("ID", '"_:blank"', "_:blank", []),
        ("ID", '"http://example.com/test"', "http://example.com/test", []),
        ("ID", '"not-iri"', Progress.VALIDATION_FAILS, []),
        #
        # Date Time
        (
            "TestClassDatetimestampScalarProp",
            "time.Unix(0, 0).UTC()",
            "1970-01-01 00:00:00 +0000 UTC",
            ["time"],
        ),
        (
            "TestClassDatetimestampScalarProp",
            'time.Date(1970, 1, 1, 3, 25, 45, 0, time.FixedZone("TST", 4800))',
            "1970-01-01 03:25:45 +0120 TST",
            ["time"],
        ),
        (
            "TestClassDatetimestampScalarProp",
            'time.Date(1970, 1, 1, 3, 25, 45, 0, time.FixedZone("TST", -4800))',
            "1970-01-01 03:25:45 -0120 TST",
            ["time"],
        ),
        # Implicit constructor not allowed
        ("TestClassDatetimestampScalarProp", "0", Progress.COMPILE_FAILS, ["time"]),
        ("TestClassDatetimestampScalarProp", "1.0", Progress.COMPILE_FAILS, ["time"]),
        (
            "TestClassDatetimestampScalarProp",
            GO_STRING,
            Progress.COMPILE_FAILS,
            ["time"],
        ),
    ],
)
def test_scalar_prop_validation(compile_test, prop, value, expect, imports):
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
        imports=imports,
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
def test_ref_prop_validation(compile_test, prop, value, expect):
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


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # Blank node assignment
        (
            "TestClassClassProp",
            '"_:blank"',
            "IRI _:blank",
        ),
        (
            "TestClassClassProp",
            '"http://example.com/test"',
            "IRI http://example.com/test",
        ),
        # Named individual assignment
        (
            "TestClassClassProp",
            "model.TestClassNamed",
            "IRI http://example.org/test-class/named",
        ),
        # Self assignment by string
        (
            "TestClassClassProp",
            "c.ID().Get()",
            "IRI _:c",
        ),
        # Ref assignment
        (
            "TestClassClassProp",
            "model.MakeObjectRef[model.TestClass](d)",
            Progress.COMPILE_FAILS,
        ),
    ],
)
def test_ref_prop_iri_short_validation(compile_test, prop, value, expect):
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
        err = c.{prop}().SetIRI(v)
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


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        # Blank node assignment
        (
            "TestClassClassProp",
            '"_:blank"',
            Progress.COMPILE_FAILS,
        ),
        # Derived assignment
        (
            "TestClassClassProp",
            "d",
            "OBJECT _:d",
        ),
        # Parent assignment
        (
            "TestClassClassProp",
            "p",
            Progress.COMPILE_FAILS,
        ),
        # Self assignment
        (
            "TestClassClassProp",
            "c",
            "OBJECT _:c",
        ),
        # Derived assignment
        (
            "TestClassClassProp",
            "d",
            "OBJECT _:d",
        ),
        # Non derived class assignment
        (
            "TestClassClassProp",
            "a",
            Progress.COMPILE_FAILS,
        ),
    ],
)
def test_ref_prop_obj_short_validation(compile_test, prop, value, expect):
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
        err = c.{prop}().SetObj(v)
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


def test_empty_property_assignment(compile_test):
    compile_test(
        """\
        p := model.MakeLinkClass()
        derived_2 := model.MakeLinkDerived2Class()
        p.LinkClassDerivedProp().SetObj(derived_2)
        """,
        progress=Progress.COMPILE_FAILS,
    )


def test_roundtrip(tmp_path, roundtrip, roundtrip_test):
    out_file = tmp_path / "out.json"

    roundtrip_test(roundtrip, out_file)

    with roundtrip.open("r") as f:
        expect = json.load(f)

    with out_file.open("r") as f:
        actual = json.load(f)

    assert expect == actual


@timetests.datetime_decode_tests()
def test_datetime_decode(compile_test, value, expect):
    output = compile_test(
        f"""\
        t, err := model.DecodeDateTime("{value}", model.Path{{}}, make(map[string]string), nil)
        if err != nil {{
            return err
        }}

        fmt.Println(t.Format(time.RFC3339))
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
        imports=["time"],
    )

    if expect is not None:
        if expect.utcoffset():
            s = expect.isoformat()
        else:
            s = expect.strftime("%Y-%m-%dT%H:%M:%SZ")

        assert (
            output.rstrip() == s
        ), f"Test failed. Expected {s!r}, got {output.rstrip()!r}"


@timetests.datetimestamp_decode_tests()
def test_datetimestamp_decode(compile_test, value, expect):
    output = compile_test(
        f"""\
        t, err := model.DecodeDateTimeStamp("{value}", model.Path{{}}, make(map[string]string), nil)
        if err != nil {{
            return err
        }}

        fmt.Println(t.Format(time.RFC3339))
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
        imports=["time"],
    )

    if expect is not None:
        if expect.utcoffset():
            s = expect.isoformat()
        else:
            s = expect.strftime("%Y-%m-%dT%H:%M:%SZ")

        assert (
            output.rstrip() == s
        ), f"Test failed. Expected {s!r}, got {output.rstrip()!r}"


@timetests.datetime_encode_tests()
def test_datetime_encode(compile_test, value, expect):
    output = compile_test(
        f"""\
        t, err := model.EncodeDateTime(
            time.Date(
                {value.year},
                {value.month},
                {value.day},
                {value.hour},
                {value.minute},
                {value.second},
                {value.microsecond * 1000},
                time.FixedZone("TST", {value.utcoffset().total_seconds()})),
            model.Path{{}},
            make(map[string]string),
            nil)
        if err != nil {{
            return err
        }}

        fmt.Println(t)
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
        imports=["time"],
    )

    if expect is not None:
        assert (
            output.rstrip() == expect
        ), f"Test failed. Expected {expect!r}, got {output.rstrip()!r}"


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


@jsonvalidation.link_tests()
def test_links(filename, name, expect_tag, tmp_path, test_context_url, link_test):
    data_file = tmp_path / "data.json"
    data_file.write_text(
        filename.read_text().replace("@CONTEXT_URL@", test_context_url)
    )

    link_test(data_file, name, expect_tag, check=True)
