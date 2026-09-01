# SPDX 3 model fixtures

Vendored, pinned snapshots of the SPDX 3 ontology, used by
`tests/test_python_spdx_protocols.py` to exercise codegen against a real,
large-scale model.
Fetched once and committed rather than downloaded at test time, so the tests
are deterministic and offline.

## Contents

| Directory   | Version                | Source                                                         |
|-------------|------------------------|----------------------------------------------------------------|
| `3.0.1/`    | SPDX 3.0.1 (stable)    | <https://spdx.org/rdf/3.0/spdx-model.ttl>                        |
|             |                        | <https://spdx.org/rdf/3.0/spdx-json-serialize-annotations.ttl>   |
|             |                        | <https://spdx.org/rdf/3.0/spdx-context.jsonld>                   |
| `3.1-dev/`  | SPDX 3.1 (pre-release) | <https://spdx.org/rdf/3.1/spdx-model.ttl>                        |
|             |                        | <https://spdx.org/rdf/3.1/spdx-json-serialize-annotations.ttl>   |
|             |                        | <https://spdx.org/rdf/3.1/spdx-context.jsonld>                   |

Fetched: 2026-08-28.

## License

These files are from the [spdx/spdx-3-model](https://github.com/spdx/spdx-3-model)
repository, published by the SPDX Working Group under the
[Community Specification License 1.0](https://github.com/spdx/spdx-3-model/blob/develop/License.md).
