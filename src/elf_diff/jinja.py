# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#

from elf_diff.document_explorer import (
    DocumentExplorer,
    StringSink,
    dumpTreeTxt,
)
from elf_diff.settings import Settings
from elf_diff.pair_report_document import getDocumentTreesOfDynamicTreeNodes
from elf_diff.string_diff import tagStringDiffSource
import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import sys
import codecs
from typing import Dict, Any


class Configurator(object):
    def __init__(self, settings: Settings, template_dir: str):
        self.settings: Settings = settings
        self.template_dir: str = template_dir

    def configureTemplate(
        self, template_file: str, template_keywords: Dict[str, Any]
    ) -> str:
        """Configure a Jinja2 template file from a set of keyword definitions. The configured content is returned as a string."""

        loader = FileSystemLoader(self.template_dir)
        env = Environment(  # nosec # silence bandid warning (we are generating static code, there's no security risk without autoescaping)
            loader=loader,
            undefined=StrictUndefined,
            autoescape=False,
        )

        # Define custom functions that are available in Jinja templates
        env.globals[
            "include_raw"
        ] = lambda file_path, loader=loader, env=env: loader.get_source(env, file_path)[
            0
        ]

        iso_8859_1_loader = FileSystemLoader(self.template_dir, encoding="ISO-8859-1")
        env.globals[
            "include_raw_iso_8859_1"
        ] = lambda file_path, loader=iso_8859_1_loader, env=env: loader.get_source(
            env, file_path
        )[
            0
        ]

        env.globals["dump_tree"] = dumpTreeTxt
        env.globals[
            "dump_tree_full"
        ] = lambda value_tree_node, display_values: dumpTreeTxt(
            value_tree_node, display_values, only_base_tree=False
        )
        env.globals["dump_leaf_paths"] = lambda node: DocumentExplorer(
            StringSink
        ).dumpDocumentLeafPaths(node)
        env.globals[
            "get_dynamic_node_document_trees"
        ] = getDocumentTreesOfDynamicTreeNodes

        env.globals["tag_string_diff"] = tagStringDiffSource

        try:
            creator = env.get_template(template_file)

        except jinja2.exceptions.TemplateError as e:
            raise Exception(
                f"Failed creating jinja creator for file '{template_file}'\n" + str(e)
            )

        try:
            sys.stdout.flush()
            replacedContent = creator.render(template_keywords)
        except (jinja2.exceptions.TemplateError) as e:
            raise Exception(
                "Failed rendering jinja template '" + template_file + "'\n" + str(e)
            )

        return replacedContent

    def configureTemplateWrite(
        self, template_file: str, output_file: str, template_keywords: Dict[str, Any]
    ) -> None:
        """Configure a Jinja2 template file and write the configured output to an output file"""
        with codecs.open(output_file, "w", "utf-8") as f:
            configured_content: str = self.configureTemplate(
                template_file, template_keywords
            )
            f.write(configured_content)
