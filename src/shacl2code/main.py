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

from . import Model, UrlContext, ContextData
from .version import VERSION
from .lang import LANGUAGES


def main(args=None):
    def handle_generate(args):
        if "://" in args.input:
            with urllib.request.urlopen(args.input) as url:
                model_data = json.load(url)
        elif args.input == "-":
            model_data = json.load(sys.stdin)
        else:
            with Path(args.input).open("r") as f:
                model_data = json.load(f)

        contexts = []
        for c in args.context:
            with urllib.request.urlopen(c) as f:
                data = json.load(f)
            contexts.append(ContextData(data, c))

        for location, url in args.context_url:
            if "://" in location:
                with urllib.request.urlopen(location) as f:
                    data = json.load(f)
            else:
                with Path(location).open("r") as f:
                    data = json.load(f)
            contexts.append(ContextData(data, url))

        m = Model(model_data, UrlContext(contexts))

        render = args.lang(args)
        render.output(m)
        return 0

    def handle_list(args):
        width = max(len(lang) for lang in LANGUAGES)
        for k, v in LANGUAGES.items():
            if args.short:
                print(k)
            else:
                print(f"{k:{width}} - {v.HELP}")

        return 0

    def handle_version(args):
        print(VERSION)
        return 0

    parser = argparse.ArgumentParser(
        description=f"Convert JSON-LD model to python. Version {VERSION}"
    )
    command_subparser = parser.add_subparsers(
        title="command",
        description="Command to execute",
        required=True,
    )
    generate_parser = command_subparser.add_parser(
        "generate",
        help="Generate language bindings",
    )
    generate_parser.add_argument(
        "--input",
        "-i",
        help="Input JSON-LD model (path, URL, or '-')",
        required=True,
    )
    generate_parser.add_argument(
        "--context",
        "-x",
        help="Require context for output (URL)",
        action="append",
        default=[],
    )
    generate_parser.add_argument(
        "--context-url",
        "-u",
        help="Require context from LOCATION (path or URL), but report as URL in generated code",
        nargs=2,
        metavar=("LOCATION", "URL"),
        action="append",
        default=[],
    )
    generate_parser.set_defaults(func=handle_generate)

    lang_subparser = generate_parser.add_subparsers(
        title="language",
        description="Language to generate",
        required=True,
    )
    for k, v in LANGUAGES.items():
        p = lang_subparser.add_parser(k, help=v.HELP)
        v.get_arguments(p)
        p.set_defaults(lang=v)

    list_parser = command_subparser.add_parser("list", help="List languages")
    list_parser.add_argument(
        "--short",
        "-s",
        action="store_true",
        help="Only list languages without descriptions",
    )
    list_parser.set_defaults(func=handle_list)

    version_parser = command_subparser.add_parser("version", help="Show version")
    version_parser.set_defaults(func=handle_version)

    parsed_args = parser.parse_args(args)

    return parsed_args.func(parsed_args)
