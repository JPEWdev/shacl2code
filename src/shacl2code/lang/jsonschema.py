# SPDX-FileContributor: Joshua Watt
# SPDX-FileContributor: Arthit Suriyawongkul
# SPDX-FileCopyrightText: 2024-present Joshua Watt
# SPDX-FileType: SOURCE
# SPDX-License-Identifier: MIT
"""JSON Schema renderer"""

import keyword
import re

from .common import BasicJinjaRender
from .lang import TEMPLATE_DIR, language


def varname(*name):
    name = str("_".join(name)).replace("@", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    while keyword.iskeyword(name):
        name = name + "_"
    return name


@language("jsonschema")
class JsonSchemaRender(BasicJinjaRender):
    HELP = "JSON Schema"

    def __init__(self, args):
        super().__init__(args, TEMPLATE_DIR / "jsonschema.j2")
        self.__render_args = {
            "schema_title": args.title,
            "schema_id": args.id,
            "allow_elided_lists": args.allow_elided_lists,
            "use_additional_properties": args.use_additional_properties,
        }

    @classmethod
    def get_arguments(cls, parser):
        super().get_arguments(parser)

        parser.add_argument("--title", help="Schema title")
        parser.add_argument("--id", help="Schema ID")
        parser.add_argument(
            "--allow-elided-lists",
            action="store_true",
            help="Allow lists to be elided if they only contain a single element",
        )
        parser.add_argument(
            "--use-additional-properties",
            action="store_true",
            help=(
                "Use additionalProperties instead of unevaluatedProperties. "
                "Flattens inherited property refs into each class definition for "
                "better compatibility with validators that have poor "
                "unevaluatedProperties performance."
            ),
        )

    def get_extra_env(self):
        return {
            "varname": varname,
        }

    def get_extra_model_env(self, classes):
        def get_all_properties(cls):
            """Return [(defining_class, prop), ...] for cls and all ancestors, parent-first, no duplicates."""
            seen = set()
            result = []

            def collect(c):
                for parent_id in c.parent_ids:
                    collect(classes.get(parent_id))
                for prop in c.properties:
                    if prop.path not in seen:
                        seen.add(prop.path)
                        result.append((c, prop))

            collect(cls)
            return result

        return {"get_all_properties": get_all_properties}

    def get_additional_render_args(self, model):
        return self.__render_args
