# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------ | -------: | -------: | ------: | --------: |
| src/shacl2code/\_\_init\_\_.py      |        4 |        0 |    100% |           |
| src/shacl2code/\_\_main\_\_.py      |        4 |        4 |      0% |      7-12 |
| src/shacl2code/context.py           |      158 |        1 |     99% |       168 |
| src/shacl2code/lang/\_\_init\_\_.py |        6 |        0 |    100% |           |
| src/shacl2code/lang/common.py       |       92 |       62 |     33% |26-30, 35-36, 41, 44, 47, 50-70, 77-136, 160-162, 175 |
| src/shacl2code/lang/cpp.py          |       64 |       38 |     41% |16-24, 28-36, 40, 44, 48, 97-104, 136-183, 186, 218 |
| src/shacl2code/lang/golang.py       |      127 |      100 |     21% |43-58, 62, 66, 70, 74, 78, 82-114, 120, 124-163, 167-206, 236-238, 259-262, 265, 279 |
| src/shacl2code/lang/jinja.py        |       12 |        1 |     92% |        17 |
| src/shacl2code/lang/jsonschema.py   |       26 |        9 |     65% |14-18, 26-27, 46, 51 |
| src/shacl2code/lang/lang.py         |        8 |        0 |    100% |           |
| src/shacl2code/lang/python.py       |       26 |       11 |     58% |14-25, 33-34, 49, 54 |
| src/shacl2code/main.py              |       69 |       26 |     62% |24-29, 34, 38-40, 43-49, 53-55, 58-65, 68-69 |
| src/shacl2code/model.py             |      181 |       39 |     78% |113, 124, 143-146, 164, 167, 204-207, 219-220, 232, 241-242, 254-255, 269-301 |
| src/shacl2code/urlcontext.py        |       13 |        1 |     92% |        23 |
| src/shacl2code/version.py           |        1 |        0 |    100% |           |
|                           **TOTAL** |  **791** |  **292** | **63%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/JPEWdev/shacl2code/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/JPEWdev/shacl2code/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FJPEWdev%2Fshacl2code%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/JPEWdev/shacl2code/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.