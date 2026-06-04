#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import json
import os
import subprocess
import textwrap
from enum import Enum
from pathlib import Path

import pytest

from testfixtures import jsonvalidation, timetests

THIS_FILE = Path(__file__)
THIS_DIR = THIS_FILE.parent

DATA_DIR = THIS_DIR / "data"

TEST_MODEL = THIS_DIR / "data" / "model" / "test.ttl"

TEST_CONTEXT = THIS_DIR / "data" / "model" / "test-context.json"

SPDX3_CONTEXT_URL = "https://spdx.github.io/spdx-3-model/context.json"


class Progress(Enum):
    COMPILE_FAILS = 0
    RUN_FAILS = 1
    VALIDATION_FAILS = 2
    RUNS = 3


def _build_rust_prog(test_lib, tmp_path, name, code):
    """Build a Rust binary crate that depends on the generated library."""
    (tmp_path / "src").mkdir(exist_ok=True)

    cargo_toml = tmp_path / "Cargo.toml"
    cargo_toml.write_text(textwrap.dedent(f"""\
            [package]
            name = "{name}"
            version = "0.1.0"
            edition = "2021"

            [dependencies]
            shacl_model = {{ path = "{test_lib}" }}
            serde_json = "1"
            """))

    src = tmp_path / "src" / "main.rs"
    src.write_text(code)

    subprocess.run(
        ["cargo", "build", "--release"],
        cwd=tmp_path,
        check=True,
    )

    return tmp_path / "target" / "release" / name


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
            "rust",
            "--output",
            libdir / "shacl_model",
        ],
        check=True,
    )

    subprocess.run(
        ["cargo", "build"],
        cwd=libdir / "shacl_model",
        check=True,
    )

    return libdir / "shacl_model"


@pytest.fixture
def compile_test(test_lib, tmp_path):
    def f(code_fragment, *, passes=True, progress=None):
        # Support both old 'passes' API and new 'progress' API
        if progress is None:
            progress = Progress.RUNS if passes else Progress.COMPILE_FAILS

        # Create a test binary crate that depends on the generated library
        (tmp_path / "src").mkdir(exist_ok=True)

        cargo_toml = tmp_path / "Cargo.toml"
        cargo_toml.write_text(
            textwrap.dedent(f"""\
                [package]
                name = "test_prog"
                version = "0.1.0"
                edition = "2021"

                [dependencies]
                shacl_model = {{ path = "{test_lib}" }}
                serde_json = "1"
                chrono = {{ version = "0.4", features = ["serde"] }}
                """))

        src = tmp_path / "src" / "main.rs"
        src.write_text(
            textwrap.dedent("""\
                use shacl_model::*;
                use std::process;

                fn test_func() -> Result<(), shacl_model::Error> {
                """)
            + textwrap.dedent(code_fragment)
            + textwrap.dedent("""\

                    Ok(())
                }

                fn main() {
                    match test_func() {
                        Ok(()) => process::exit(0),
                        Err(e) => {
                            match &e {
                                shacl_model::Error::Validation(_, _) => {
                                    eprintln!("VALIDATION_FAILS {}", e);
                                }
                                _ => {
                                    eprintln!("ERROR {}", e);
                                }
                            }
                            process::exit(1);
                        }
                    }
                }
                """)
        )

        p = subprocess.run(
            ["cargo", "build", "--release"],
            cwd=tmp_path,
            capture_output=True,
            encoding="utf-8",
        )

        if progress == Progress.COMPILE_FAILS:
            assert (
                p.returncode != 0
            ), f"Compile succeeded when failure was expected. Output: {p.stdout}"
            return None

        assert (
            p.returncode == 0
        ), f"Compile failed. stderr: {p.stderr}\nstdout: {p.stdout}"

        prog = tmp_path / "target" / "release" / "test_prog"

        p = subprocess.run(
            [prog],
            capture_output=True,
            encoding="utf-8",
        )

        if progress == Progress.RUN_FAILS:
            assert (
                p.returncode != 0
            ), f"Run succeeded when failure was expected. Output: {p.stdout}"
            return None

        if progress == Progress.VALIDATION_FAILS:
            assert (
                p.returncode != 0
            ), f"Run succeeded when validation failure was expected. Output: {p.stdout}"
            assert (
                "VALIDATION_FAILS" in p.stderr
            ), f"VALIDATION_FAILS was not raised in program. stderr: {p.stderr}"
            return None

        assert p.returncode == 0, f"Run failed. stderr: {p.stderr}\nstdout: {p.stdout}"
        return p.stdout

    yield f


@pytest.fixture(scope="module")
def validate_test(test_lib, tmp_path_factory):
    """Build a validation program that reads JSON-LD and validates it."""
    tmp_path = tmp_path_factory.mktemp("validate")

    prog = _build_rust_prog(
        test_lib,
        tmp_path,
        "validate",
        textwrap.dedent("""\
            use shacl_model::*;
            use std::fs::File;
            use std::io::BufReader;

            fn main() {
                let args: Vec<String> = std::env::args().collect();
                let file = File::open(&args[1]).expect("Failed to open file");
                let reader = BufReader::new(file);

                let mut objset = SHACLObjectSet::new();
                if let Err(e) = objset.decode(reader) {
                    eprintln!("Decode error: {}", e);
                    std::process::exit(1);
                }

                if !objset.validate(None) {
                    eprintln!("Validation failed");
                    std::process::exit(1);
                }
            }
            """),
    )

    def f(path, passes):
        p = subprocess.run(
            [prog, path],
            capture_output=True,
            encoding="utf-8",
        )
        if passes:
            assert (
                p.returncode == 0
            ), f"Validation failed when a pass was expected. stderr: {p.stderr}"
        else:
            assert p.returncode != 0, f"Validation passed when a failure was expected"

    yield f


@pytest.fixture(scope="module")
def roundtrip_test(test_lib, tmp_path_factory):
    """Build a roundtrip program that reads JSON-LD, decodes, re-encodes."""
    tmp_path = tmp_path_factory.mktemp("roundtrip")

    prog = _build_rust_prog(
        test_lib,
        tmp_path,
        "roundtrip",
        textwrap.dedent("""\
            use shacl_model::*;
            use std::fs::File;
            use std::io::{BufReader, BufWriter};

            fn main() {
                let args: Vec<String> = std::env::args().collect();

                let in_file = File::open(&args[1]).expect("Failed to open input file");
                let reader = BufReader::new(in_file);

                let mut objset = SHACLObjectSet::new();
                objset.decode(reader).expect("Failed to decode");

                let out_file = File::create(&args[2]).expect("Failed to create output file");
                let writer = BufWriter::new(out_file);

                objset.encode(writer).expect("Failed to encode");
            }
            """),
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
    """Build a link test program that checks reference resolution."""
    tmp_path = tmp_path_factory.mktemp("link")

    prog = _build_rust_prog(
        test_lib,
        tmp_path,
        "link",
        textwrap.dedent("""\
            use shacl_model::*;
            use std::fs::File;
            use std::io::BufReader;

            fn main() {
                let args: Vec<String> = std::env::args().collect();

                let file = File::open(&args[1]).expect("Failed to open file");
                let reader = BufReader::new(file);

                let mut objset = SHACLObjectSet::new();
                objset.decode(reader).expect("Failed to decode");

                if !objset.validate(None) {
                    eprintln!("Validation failed");
                    std::process::exit(1);
                }

                // Find the check object by ID (args[2]) and the expected object by tag (args[3])
                let mut check_idx: Option<usize> = None;
                let mut expect_idx: Option<usize> = None;

                for (idx, obj) in objset.objects().iter().enumerate() {
                    if let Some(lc) = obj.downcast_ref::<LinkClass>() {
                        if let Some(id) = lc.id() {
                            if id == args[2] {
                                check_idx = Some(idx);
                            }
                        }
                        if let Some(ref tag) = lc.link_class_tag {
                            if *tag == args[3] {
                                expect_idx = Some(idx);
                            }
                        }
                    }
                    if let Some(lc) = obj.downcast_ref::<LinkDerivedClass>() {
                        if let Some(id) = lc.id() {
                            if id == args[2] {
                                check_idx = Some(idx);
                            }
                        }
                        if let Some(ref tag) = lc.link_class_tag {
                            if *tag == args[3] {
                                expect_idx = Some(idx);
                            }
                        }
                    }
                }

                let check_idx = check_idx.unwrap_or_else(|| {
                    eprintln!("Unable to find node {}", args[2]);
                    std::process::exit(1);
                });

                let _expect_idx = expect_idx.unwrap_or_else(|| {
                    eprintln!("Unable to find tag {}", args[3]);
                    std::process::exit(1);
                });

                let check = &objset.objects()[check_idx];

                let check_link_prop = |name: &str, r: &Option<Ref>| {
                    let r = r.as_ref().unwrap_or_else(|| {
                        eprintln!("Reference is nil for {}", name);
                        std::process::exit(1);
                    });

                    match r {
                        Ref::Object(_) => {},
                        Ref::IRI(iri) => {
                            eprintln!("Reference in {} does not refer to an object, has IRI {}", name, iri);
                            std::process::exit(1);
                        }
                    }
                };

                // Check properties based on the type
                if let Some(lc) = check.downcast_ref::<LinkClass>() {
                    check_link_prop("link_class_link_prop", &lc.link_class_link_prop);
                    check_link_prop("link_class_link_prop_no_class", &lc.link_class_link_prop_no_class);
                    for (i, r) in lc.link_class_link_list_prop.iter().enumerate() {
                        check_link_prop(&format!("link_class_link_list_prop[{}]", i), &Some(r.clone()));
                    }
                } else if let Some(lc) = check.downcast_ref::<LinkDerivedClass>() {
                    check_link_prop("link_class_link_prop", &lc.link_class_link_prop);
                    check_link_prop("link_class_link_prop_no_class", &lc.link_class_link_prop_no_class);
                    for (i, r) in lc.link_class_link_list_prop.iter().enumerate() {
                        check_link_prop(&format!("link_class_link_list_prop[{}]", i), &Some(r.clone()));
                    }
                } else {
                    eprintln!("Check object is not a LinkClass");
                    std::process::exit(1);
                }
            }
            """),
    )

    def f(path, name, tag, **kwargs):
        subprocess.run(
            [prog, path, name, tag],
            encoding="utf-8",
            check=True,
        )

    yield f


@pytest.mark.parametrize(
    "args",
    [
        ["--input", TEST_MODEL],
        ["--input", TEST_MODEL, "--context-url", TEST_CONTEXT, SPDX3_CONTEXT_URL],
    ],
)
class TestOutput:
    def test_output_compile(self, tmp_path, model_server, args):
        subprocess.run(
            [
                "shacl2code",
                "generate",
                "--context",
                model_server + "/test-context.json",
            ]
            + args
            + [
                "rust",
                "--output",
                tmp_path / "shacl_model",
            ],
            check=True,
        )

        subprocess.run(
            ["cargo", "build"],
            cwd=tmp_path / "shacl_model",
            check=True,
        )


def test_compile(compile_test):
    compile_test("")


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


def test_roundtrip(tmp_path, roundtrip, roundtrip_test):
    out_file = tmp_path / "out.json"

    roundtrip_test(roundtrip, out_file)

    with roundtrip.open("r") as f:
        expect = json.load(f)

    with out_file.open("r") as f:
        actual = json.load(f)

    assert expect == actual


@jsonvalidation.link_tests()
def test_links(filename, name, expect_tag, tmp_path, test_context_url, link_test):
    data_file = tmp_path / "data.json"
    data_file.write_text(
        filename.read_text().replace("@CONTEXT_URL@", test_context_url)
    )

    link_test(data_file, name, expect_tag, check=True)


@jsonvalidation.context_tests()
def test_objset_context(compile_test, context, expanded, compacted):
    program = ["let mut objset = SHACLObjectSet::new();"]

    for k, v in context.items():
        program.append(f'objset.add_context("{k}".to_string(), "{v}".to_string());')

    program.append(f'println!("{{}}", objset.compact_iri("{expanded}"));')
    program.append(f'println!("{{}}", objset.expand_iri("{compacted}"));')

    output = compile_test("\n".join(program))

    assert output.splitlines() == [compacted, expanded]


RUST_STRING = '"string".to_string()'


@pytest.mark.parametrize(
    "prop,value,expect",
    [
        #
        # Positive integer
        ("test_class_positive_integer_prop", "1i64", "1"),
        ("test_class_positive_integer_prop", "-1i64", Progress.VALIDATION_FAILS),
        ("test_class_positive_integer_prop", "0i64", Progress.VALIDATION_FAILS),
        # String value
        ("test_class_positive_integer_prop", RUST_STRING, Progress.COMPILE_FAILS),
        #
        # Non-negative integer
        ("test_class_nonnegative_integer_prop", "1i64", "1"),
        ("test_class_nonnegative_integer_prop", "-1i64", Progress.VALIDATION_FAILS),
        ("test_class_nonnegative_integer_prop", "0i64", "0"),
        # String value
        (
            "test_class_nonnegative_integer_prop",
            RUST_STRING,
            Progress.COMPILE_FAILS,
        ),
        #
        # Integer
        ("test_class_integer_prop", "1i64", "1"),
        ("test_class_integer_prop", "-1i64", "-1"),
        ("test_class_integer_prop", "0i64", "0"),
        # String value
        ("test_class_integer_prop", RUST_STRING, Progress.COMPILE_FAILS),
        #
        # Float
        ("test_class_float_prop", "-1.0f64", "-1"),
        ("test_class_float_prop", "0.0f64", "0"),
        ("test_class_float_prop", "1.0f64", "1"),
        # String value
        ("test_class_float_prop", RUST_STRING, Progress.COMPILE_FAILS),
        #
        # Boolean prop
        ("test_class_boolean_prop", "true", "true"),
        ("test_class_boolean_prop", "false", "false"),
        # String value
        ("test_class_boolean_prop", RUST_STRING, Progress.COMPILE_FAILS),
        #
        # String Property
        ("test_class_string_scalar_prop", RUST_STRING, "string"),
        ("test_class_string_scalar_prop", '"".to_string()', ""),
        # Integer value
        ("test_class_string_scalar_prop", "1i64", Progress.COMPILE_FAILS),
        #
        # Enumerated value
        (
            "test_class_enum_prop",
            '"http://example.org/enumType/foo".to_string()',
            "http://example.org/enumType/foo",
        ),
        ("test_class_enum_prop", RUST_STRING, Progress.VALIDATION_FAILS),
        # Integer value
        ("test_class_enum_prop", "1i64", Progress.COMPILE_FAILS),
        #
        # Pattern validated string
        ("test_class_regex", '"foo1".to_string()', "foo1"),
        ("test_class_regex", '"foo2".to_string()', "foo2"),
        ("test_class_regex", '"foo2a".to_string()', "foo2a"),
        ("test_class_regex", '"bar".to_string()', Progress.VALIDATION_FAILS),
        ("test_class_regex", '"fooa".to_string()', Progress.VALIDATION_FAILS),
        ("test_class_regex", '"afoo1".to_string()', Progress.VALIDATION_FAILS),
        #
        # ID assignment
        ("_id", '"_:blank".to_string()', "_:blank"),
        ("_id", '"http://example.com/test".to_string()', "http://example.com/test"),
        ("_id", '"not-iri".to_string()', Progress.VALIDATION_FAILS),
    ],
)
def test_scalar_prop_validation(compile_test, prop, value, expect):
    is_id = prop == "_id"

    if is_id:
        set_code = f"obj.set_id(Some({value}));"
    else:
        set_code = f"obj.{prop} = Some({value});"

    if is_id:
        print_code = 'println!("{}", obj.id().unwrap());'
    elif isinstance(expect, Progress):
        print_code = ""
    elif isinstance(expect, str):
        print_code = f'println!("{{}}", obj.{prop}.unwrap());'
    else:
        print_code = ""

    validate_code = """\
        let path = Path::new();
        if !obj.validate(&path, None) {
            return Err(Error::Validation("test".to_string(), "Validation failed".to_string()));
        }
    """

    output = compile_test(
        f"""\
        #[allow(deprecated)]
        let mut obj = make_test_class();
        {set_code}
        {validate_code}
        {print_code}
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


@timetests.datetime_decode_tests()
def test_datetime_decode(compile_test, value, expect):
    output = compile_test(
        f"""\
        let path = Path::new();
        let dt = decode_date_time("{value}", &path)?;
        println!("{{}}", encode_date_time(&dt));
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
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
        let path = Path::new();
        let dt = decode_date_time_stamp("{value}", &path)?;
        println!("{{}}", encode_date_time(&dt));
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
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
    offset_secs = int(value.utcoffset().total_seconds())
    output = compile_test(
        f"""\
        use chrono::{{FixedOffset, TimeZone}};
        let offset = FixedOffset::east_opt({offset_secs}).unwrap();
        let dt = offset.with_ymd_and_hms({value.year}, {value.month}, {value.day}, {value.hour}, {value.minute}, {value.second}).unwrap();
        println!("{{}}", encode_date_time(&dt));
        """,
        progress=Progress.RUN_FAILS if expect is None else Progress.RUNS,
    )

    if expect is not None:
        assert (
            output.rstrip() == expect
        ), f"Test failed. Expected {expect!r}, got {output.rstrip()!r}"


def test_extensible_context(compile_test, roundtrip):
    compile_test(
        f"""\
        use std::fs::File;
        use std::io::BufReader;

        let file = File::open("{roundtrip}")?;
        let reader = BufReader::new(file);

        let mut objset = SHACLObjectSet::new();
        objset.decode(reader)?;

        let obj = objset.get_object_by_id("http://serialize.example.com/test-uses-extensible-abstract")
            .expect("Unable to find object");

        let abstract_obj = obj.downcast_ref::<UsesExtensibleAbstractClass>()
            .expect("Object is not of expected type");

        let prop_ref = abstract_obj.uses_extensible_abstract_class_prop.as_ref()
            .expect("Property not set");

        let prop_obj = prop_ref.get_object()
            .expect("Property is not an object ref");

        let inner = prop_obj.as_shacl_object();
        assert_eq!(inner.type_iri(), "http://serialize.example.com/custom-extensible",
            "Wrong type: {{}}", inner.type_iri());

        let ext_props = inner.get_ext_properties()
            .expect("No extension properties");
        assert!(ext_props.contains_key("http://custom-prop.example.com/prop"),
            "Missing extension property");
        """,
    )
