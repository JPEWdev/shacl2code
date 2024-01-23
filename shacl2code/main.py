#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import json
import sys
import urllib.request
from pathlib import Path

from . import Model
from .const import TEMPLATE_DIR
from .version import VERSION


def get_langs():
    langs = []
    for child in TEMPLATE_DIR.iterdir():
        if child.suffixes and child.suffixes[-1] == ".j2":
            langs.append(child.stem)
    return langs


def main():
    parser = argparse.ArgumentParser(
        description=f"Convert JSON-LD model to python. Version {VERSION}"
    )
    parser.add_argument(
        "--lang",
        help="Output Language",
        choices=get_langs(),
        required=True,
    )
    parser.add_argument(
        "input",
        help="Input JSON-LD model (path, URL, or '-')",
    )
    parser.add_argument(
        "output",
        help="Output file name or '-' for stdout",
    )

    args = parser.parse_args()

    if "://" in args.input:
        with urllib.request.urlopen(args.input) as url:
            model_data = json.load(url)
    elif args.input == "-":
        model_data = json.load(sys.stdin)
    else:
        with Path(args.input).open("r") as f:
            model_data = json.load(f)

    m = Model(model_data)
    render = m.render_template(args.lang)

    if args.output == "-":
        print(render)
    else:
        with Path(args.output).open("w") as f:
            f.write(render)

    return 0


if __name__ == "__main__":
    sys.exit(main())
