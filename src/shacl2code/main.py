#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import json
import sys
import urllib.request
import rdflib
from pathlib import Path

from . import Model, UrlContext, ContextData
from .version import VERSION
from .lang import LANGUAGES


def main(args=None):
    def handle_generate(parser, args):
        graph = rdflib.Graph()
        for inmodel in args.input:
            if inmodel == "-":
                if args.input_format == "auto":
                    print("ERROR: Input format must be specified with stdin")
                    parser.print_help()
                    return 1

                graph.parse(sys.stdin, format=args.input_format)
            else:
                if args.input_format == "auto":
                    graph.parse(inmodel)
                else:
                    graph.parse(inmodel, format=args.input_format)

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

        m = Model(graph, UrlContext(contexts))

        render = args.lang(args)
        render.output(m)
        return 0

    def handle_list(parser, args):
        width = max(len(lang) for lang in LANGUAGES)
        for k, v in LANGUAGES.items():
            if args.short:
                print(k)
            else:
                print(f"{k:{width}} - {v.HELP}")

        return 0

    def handle_version(parser, args):
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
        help="Input model (path, URL, or '-')",
        action="append",
        default=[],
        required=True,
    )
    generate_parser.add_argument(
        "--input-format",
        "-t",
        help="Input file format, or 'auto' to attempt to determine automatically. Default is %(default)s",
        default="auto",
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
    generate_parser.add_argument(
        "--license",
        "-l",
        help="SPDX License Identifier to use for generated source code. Default is %(default)s",
        default="0BSD",
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

    return parsed_args.func(parser, parsed_args)
