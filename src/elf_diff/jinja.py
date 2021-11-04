# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
#
# This program is free software: you can redistribute it and/or modify it under it under
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
from elf_diff.error_handling import unrecoverableError
from elf_diff.document_explorer import (
    DocumentExplorer,
    StringSink,
    TreeTraversalOptions,
)
from elf_diff.pair_report_document import getDocumentTreesOfSymbolClasses
import jinja2
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import sys
import codecs


class Configurator(object):
    def __init__(self, settings, template_dir):
        self.settings = settings
        self.template_dir = template_dir

    def configureTemplate(self, template_file, template_keywords):

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

        env.globals["dump_tree"] = lambda node, display_values: DocumentExplorer(
            StringSink, display_values=display_values
        ).dumpDocumentTree(node)
        env.globals["dump_tree_full"] = lambda node, display_values: DocumentExplorer(
            StringSink, display_values=display_values
        ).dumpDocumentTree(node, TreeTraversalOptions(visit_value_tree_nodes=True))
        env.globals["dump_leaf_paths"] = lambda node: DocumentExplorer(
            StringSink
        ).dumpDocumentLeafPaths(node)
        env.globals["get_symbol_document_trees"] = getDocumentTreesOfSymbolClasses

        try:
            creator = env.get_template(template_file)

        except jinja2.exceptions.TemplateError as e:
            unrecoverableError(
                f"Failed creating jinja creator for file '{template_file}'\n" + str(e)
            )

        try:
            sys.stdout.flush()
            replacedContent = creator.render(template_keywords)
        except (jinja2.exceptions.TemplateError) as e:
            unrecoverableError(
                "Failed rendering jinja template '" + template_file + "'\n" + str(e)
            )

        return replacedContent

    def configureTemplateWrite(self, template_file, output_file, template_keywords):

        with codecs.open(output_file, "w", "utf-8") as output_file:
            configured_content = self.configureTemplate(
                template_file, template_keywords
            )
            output_file.write(configured_content)
