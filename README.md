# Convert SHACL Model to code bindings
[![Coverage Report](https://raw.githubusercontent.com/JPEWdev/shacl2code/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

This tool can be used to convert a JSONLD SHACL model into various code
bindings

## Installation

`shacl2code` can be installed using pip:

```shell
python3 -m pip install shacl2code
```

## Usage

`shacl2code` can generate bindings from either a local file:
```shell
shacl2code generate -i model.jsonld python -o out.py
```
Or from a URL:
```shell
shacl2code generate -i https://spdx.github.io/spdx-3-model/model.jsonld python -o out.py
```
Or from stdin:
```shell
cat model.jsonld | shacl2code generate -i - python -o - > out.py
```

For more information, run:
```shell
shacl2code --help
```

The available language bindings can be viewed by running:
```shell
shacl2code list
```

## Developing

Developing on `shacl2code` is best done using a virtual environment. You can
configure one and install shacl2code in editable mode with all necessary
development dependencies by running:

```shell
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
```

## Testing

`shacl2code` has a test suite written in [pytest][pytest]. To run it, setup a
virtual environment as shown above, then run:
```shell
pytest
```

In addition to the test results, a test coverage report will also be generated
using [pytest-cov][pytest-cov]



[pytest]: https://www.pytest.org
[pytest-cov]: https://pytest-cov.readthedocs.io/en/latest/
