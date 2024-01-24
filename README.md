# Convert SHACL Model to code bindings

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
