#! /usr/bin/env python3
#
# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import sys
import subprocess

from pathlib import Path

THIS_DIR = Path(__file__).parent
DATA_DIR = THIS_DIR.parent / "data"
MODEL_DIR = DATA_DIR / "model"


def make_dest(src, lang, subdir, ext):
    return THIS_DIR / lang / subdir / (src.stem + ext)


def main():
    found = False
    for src in MODEL_DIR.iterdir():
        if not src.is_file():
            continue

        if not src.name.endswith(".jsonld") and not src.name.endswith(".ttl"):
            continue

        context = src.parent / (src.stem + "-context.json")

        for lang, ext in (("python", ".py"), ("jsonschema", ".json"), ("cpp", ""), ("golang", ".go")):
            subprocess.run(
                [
                    "shacl2code",
                    "generate",
                    f"--input={src}",
                    lang,
                    f"--output={make_dest(src, lang, 'nocontext', ext)}",
                ],
                check=True,
            )
            if context.is_file():
                subprocess.run(
                    [
                        "shacl2code",
                        "generate",
                        f"--input={src}",
                        "--context-url",
                        context,
                        "https://spdx.github.io/spdx-3-model/context.json",
                        lang,
                        f"--output={make_dest(context, lang, 'context', ext)}",
                    ],
                    check=True,
                )

        subprocess.run(
            [
                "shacl2code",
                "generate",
                f"--input={src}",
                "jinja",
                f"--output={make_dest(src, 'raw', 'nocontext', '.txt')}",
                "--template",
                DATA_DIR / "raw.j2",
            ],
            check=True,
        )

        if context.is_file():
            subprocess.run(
                [
                    "shacl2code",
                    "generate",
                    f"--input={src}",
                    "--context-url",
                    context,
                    "https://spdx.github.io/spdx-3-model/context.json",
                    "jinja",
                    f"--output={make_dest(context, 'raw', 'context', '.txt')}",
                    "--template",
                    DATA_DIR / "context.j2",
                ],
                check=True,
            )
        found = True

    if not found:
        print("No files generated")
        return 1


if __name__ == "__main__":
    sys.exit(main())
