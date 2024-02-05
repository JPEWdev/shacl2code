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

from . import Model, ContextMap
from .version import VERSION
from .lang import LANGUAGES


def main():
    def handle_generate(args):
        if "://" in args.input:
            with urllib.request.urlopen(args.input) as url:
                model_data = json.load(url)
        elif args.input == "-":
            model_data = json.load(sys.stdin)
        else:
            with Path(args.input).open("r") as f:
                model_data = json.load(f)

        if args.context:
            if "://" in args.context:
                with urllib.request.urlopen(args.context) as url:
                    context = ContextMap(
                        json.load(url), args.context_url or args.context
                    )
            else:
                if not args.context_url:
                    print("ERROR: Context URL is required for local path")
                    return 1

                with Path(args.context).open("r") as f:
                    context = ContextMap(json.load(f), args.context_url)
        else:
            context = ContextMap(None, None)

        m = Model(model_data, context)

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
        help="Require context for output (path or URL)",
    )
    generate_parser.add_argument(
        "--context-url",
        "-u",
        help="Override URL for context (required for local file)",
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

    args = parser.parse_args()

    return args.func(args)
