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

from elf_diff.plugin import ExportPairReportPlugin
from elf_diff.document_explorer import DocumentExplorer, TREE_TRAVERSAL_ALL, StringSink


class TXTExportPairReportPlugin(ExportPairReportPlugin):
    def __init__(self, settings, plugin_configuration):
        super().__init__(settings, plugin_configuration)

    def export(self, document):
        txt_output = DocumentExplorer(StringSink, display_values=True).dumpDocumentTree(
            document=document, tree_traversal_options=TREE_TRAVERSAL_ALL
        )

        with open(self.plugin_configuration["output_file"], "w") as f:
            f.write(txt_output)
