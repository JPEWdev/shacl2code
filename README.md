# Convert SHACL Model to code bindings

[![PyPI - Version](https://img.shields.io/pypi/v/shacl2code)](https://pypi.org/project/shacl2code/)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/9999/badge)](https://www.bestpractices.dev/projects/9999)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/JPEWdev/shacl2code/badge)](https://scorecard.dev/viewer/?uri=github.com/JPEWdev/shacl2code)
[![Coverage Report](https://raw.githubusercontent.com/JPEWdev/shacl2code/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

This tool can be used to convert a SHACL model into various code bindings

## Installation

`shacl2code` can be installed using pip:

```shell
python3 -m pip install shacl2code
```

## Usage

`shacl2code` can generate bindings from either a local file:

```shell
shacl2code generate -i model.jsonld python -o out
```

Or from a URL:

```shell
shacl2code generate -i https://example.com/rdf/model.jsonld python -o out
```

Or from stdin:

```shell
cat model.jsonld | shacl2code generate -i - python -o out
```

For more information, run:

```shell
shacl2code --help
```

The available language bindings can be viewed by running:

```shell
shacl2code list
```

### Using JSON-LD contexts

When using JSON-LD contexts, the context document shall align with the model.

During model development, there may be cases where the context URL is known
but not yet live or resolvable. In these situations, you can use the
`--context-url` option to map your local context file to its future public home.

The `--context-url` option accepts two arguments:

1. `CONTEXT_LOCATION`: The actual path to the local or temporary file
   containing the context.
2. `CONTEXT_URL`: The official public URL. While temporarily unresolvable
   during development, this is the URL that production JSON-LD processors will
   eventually rely on, so it must be recorded inside the generated JSON Schema.

### Generating the JSON Schema file

`shacl2code` can generate a JSON Schema directly from a model.

To view all options specific to JSON Schema generation, run:

```shell
shacl2code generate jsonschema -h
```

#### Example 1: Generating from publicly available URLs

To generate a schema using remote, publicly accessible assets
(such as SPDX 3.0.1):

```shell
shacl2code generate \
    --input https://spdx.org/rdf/3.0.1/spdx-model.ttl \
    --input https://spdx.org/rdf/3.0.1/spdx-json-serialize-annotations.ttl \
    --context https://spdx.org/rdf/3.0.1/spdx-context.jsonld \
    jsonschema \
    --output spdx-json-schema.json
```

#### Example 2: Generating with a local context document

To generate a schema using a local context file while embedding its future
public URL:

```shell
shacl2code generate \
    --input model-draft.ttl \
    --context-url context-draft.jsonld https://example.com/context.jsonld \
    jsonschema \
   --output schema.json
```

## Developing

Developing on `shacl2code` is best done using a virtual environment. You can
configure one and install shacl2code in editable mode with all necessary
development dependencies by running:

```shell
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Testing

`shacl2code` has a test suite written in [pytest][pytest]. To run it, setup a
virtual environment as shown above, then run:

```shell
pytest
```

In addition to the test results, a test coverage report will also be generated
using [pytest-cov][pytest-cov]

The test suite is quite extensive and can catch a lot of errors. When adding
new features to the code generation, please add tests to ensure that these
features continue to behave as expected.

All changes to the code are expected to pass the test suite before they merge.

## Custom Annotations

`shacl2code` supports a number of custom annotations that can be specified in a
SHACL model to give hints about the generated code. All of these annotations
live in the `https://jpewdev.github.io/shacl2code/schema#` namespace, and
commonly are given the `sh-to-code` prefix to make it easier to reference them.
For example, in Turtle one would add the prefix mapping:

```ttl
@prefix sh-to-code: <https://jpewdev.github.io/shacl2code/schema#> .
```

### ID Property Name

The `idPropertyName` annotation allows a class to specify what the name of the
"property" that specifies the RDF subject of an object is for serializations
that support it. For example, in JSON-LD, the `@id` property indicates the
subject in RDF. If you wanted to alias the `@id` property to another name, the
`idPropertyName` annotation will let you do this. For example, the following
turtle will use `MyId` instead of `@id` when writing JSON-LD bindings:

```ttl
<MyClass> a owl:Class, sh:NodeShape ;
    sh-to-code:idPropertyName "MyId"
    .
```

When doing this, the class would then look like this in JSON-LD:

```json
{
    "@type": "MyClass",
    "MyId": "http://example.com/id"
}
```

The `idPropertyName` annotation is inherited by derived classes, so for example
any class that derived from `MyClass` would also use `MyId` as the subject
property.

**Note:** This only specifies what the name of the field should be in generated
bindings and has no bearing on how an RDF parser would interpret the property.
In order to still be parsed by RDF, you would also need context file that maps
`MyId` to `@id`, for example:

```json
{
    "@context": {
        "MyId": "@id"
    }
}
```

`shacl2code` doesn't do this for you, nor does it validate that you have done
it.

### Extensible Classes

Most bindings generated from `shacl2code` are "closed" in that they do not
allow extra properties to be added to object outside of what is specified in
model. This ensures that field name typos and other unintended properties are
not added to an object. However, in some cases a class may be specifically
intended to be extended such that arbitrary fields can be added to it, which
can be done using the `isExtensible` property. This is a boolean property that
indicates if a class can be extended, and defaults to `false`. For example, the
following turtle will declare a class as extensible:

```ttl
<MyClass> a owl:Class, sh:NodeShape ;
    sh-to-code:isExtensible true
    .
```

The `isExtensible` property is _not_ inherited by derived classes, meaning it
is possible to have a class derived from `MyClass` which is itself not
extensible.

The mechanism for dealing with extensible classes will vary between the
different bindings, but in general it means that they will not be very picky
about object types and properties in any location where an extensible class is
allowed.

**Note**: You may want to be careful about where and how many extensible
classes are allowed in your model. If there are too many and they are allowed
anywhere, it may mean that typos in object types (e.g. `@type` in JSON-LD) are
not caught by validation as they will have to be assumed to be a derived class
from an extensible type.

### Abstract Classes

By default, classes generated by `shacl2code` are all instantiable (i.e. they
can be created). In some instances, it may be desirable to declare a class as
abstract (meaning that it cannot be instantiated, but non-abstract derived
classes can). There are several ways of marking a class as abstract listed
below, in order of preference (with the most preferred being first).

#### SHACL Validated Abstract Classes

A class can be prevented from being directly instantiated using SHACL by adding
a constraint on the shape that it cannot be of its own type. This can be done
with the following turtle:

```ttl
<MyClass> a owl:Class, sh:NodeShape ;
    # SHACL to prevent a class from being instantiated as this exact type
    sh:property [
        sh:path rdf:type ;
        sh:not [ sh:hasValue <MyClass> ]
    ] .
```

`shacl2code` will detect this pattern and generate abstract bindings for
`MyClass`.

This method is most preferred, since it is enforced by SHACL and not just
`shacl2code` bindings

#### shacl2code Annotation

`shacl2code` has a custom annotation that can be used to mark a class as
abstract. This can be done with the boolean `isAbstract` property. For
example, the following turtle will declare a class as abstract:

```ttl
<MyClass> a owl:Class, sh:NodeShape ;
    sh-to-code:isAbstract true
    .
```

The `isAbstract` property is _not_ inherited by derived classes, so any derived
classes are automatically concrete unless they indicate otherwise.

#### SPDX Abstract Class Parent

It is also possible to define a class as abstract by declaring it to be of
type: `http://spdx.invalid./AbstractClass`, but this is not preferred.

### Pre-Release models

`shacl2code` can detect if an ontology is a "pre-release" version (still
subject to breaking changes). For language bindings that support it (such as
Python), importing a pre-release ontology binding will emit a warning
(e.g. `FutureWarning`).

Pre-release status can be specified explicitly via command-line options,
or inferred automatically from various ontology annotations. For example,

```ttl
<http://example.org/my-ontology> a ow:Ontology ;
   sh-to-code:isPreRelease true
   .
```

Note that the IRI of the ontology must be the prefix of all IRIs that belong to
that ontology.

In the event of conflicting annotations, `shacl2code` evaluates pre-release
status using the following order of precedence (1 = the highest priority):

1. **`--pre-release` or `--no-pre-release` command-line options**:
   Explicitly marks the generated bindings as pre-release or stable,
   overriding any annotations in the input ontology.
2. **`sh-to-code:isPreRelease`**:
   The `shacl2code` custom boolean annotation
   (`sh-to-code:isPreRelease true` or `false`).
3. **`adms:status` (EU SEMIC Vocabulary)**:
   If the status is
   `<http://publications.europa.eu/resource/authority/dataset-status/DEVELOP>`,
   it is considered a pre-release.
   Other values in the dataset-status vocabulary space (e.g. `COMPLETED`)
   indicate a stable release.
4. **`adms:status` (Original ADMS Vocabulary)**:
   If the status is `<http://purl.org/adms/status/UnderDevelopment>`,
   it is considered a pre-release.
   Other values in the ADMS status namespace (e.g. `Completed`)
   indicate a stable release.
5. **`bibo:status` (Bibliographic Ontology)**:
   If set to `<http://purl.org/ontology/bibo/status/draft>`, it is
   considered a pre-release.
   Other values in the BIBO status namespace (e.g. `published`, `legal`)
   indicate a stable release.
6. **`schema:creativeWorkStatus`**:
   If set to `"Draft"` or `"Incomplete"`, it is considered a pre-release.
   Other values (e.g. `"Published"`) indicate a stable release.
7. **`vs:term_status`**:
   If set to `"unstable"` or `"testing"`, it is considered a pre-release.
   Other values (e.g. `"stable"`) indicate a stable release.
8. **`owl:versionInfo` (pre-release extension)**:
   If the version string contains a pre-release extension suffix
   (e.g., `-alpha`, `-beta`, `-dev`, `-rc`, `-SNAPSHOT`, `.alpha`, etc.).
9. **`owl:versionInfo` (major version zero)**:
   If the version string corresponds to a major version zero in
   [Semantic Versioning][semver] (e.g., `0.7.1`).
10. **Default Fallback**:
    If none of the above are present, the ontology is assumed to be a stable
    release.

[pytest]: https://www.pytest.org
[pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/
[semver]: https://semver.org/
