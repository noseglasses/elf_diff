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

from elf_diff.plugin import (
    ExportPairReportPlugin,
    PluginConfigurationKey,
    PluginConfigurationInformation,
)
from elf_diff.error_handling import warning
from elf_diff.plugins.export.html.plugin import HTMLExportPairReportPlugin
from elf_diff.pair_report_document import ValueTreeNode
import tempfile
import os
from typing import Dict


def convertHTMLToPDF(html_file: str, pdf_file: str):
    """Convert a HTML file to a PDF file"""
    try:
        # Weasyprint is not available on all platforms.
        # Therefore, we import it on function level and
        # tolerate it not being available.
        from weasyprint import HTML  # type: ignore # Make mypy ignore this module
    except ImportError:
        warning("Unable to import module weasyprint")
        warning("No pdf export supported")
    else:
        HTML(html_file).write_pdf(pdf_file)


class PDFExportPairReportPlugin(ExportPairReportPlugin):
    """A plugin class that exports the elf_diff document as a PDF document"""

    def __init__(self, settings, plugin_configuration):
        super().__init__(settings, plugin_configuration)
        self._tmp_html_file: str

    def cleanup(self) -> None:
        """Cleanup the temporary HTML file"""
        if os.path.isfile(self._tmp_html_file):
            os.remove(self._tmp_html_file)

    def export(self, document: ValueTreeNode) -> None:
        """Export the PDF document"""

        pdf_output_file: str = self.getConfigurationParameter("output_file")

        try:
            with tempfile.TemporaryDirectory() as tmp:
                self._tmp_html_file = os.path.join(tmp, "tmp_html_file.html")

                # use path
                plugin_configuration: Dict[str, str] = {
                    "single_page": "True",
                    "output_file": self._tmp_html_file,
                    "quiet": "True",
                }
                html_export_plugin = HTMLExportPairReportPlugin(
                    self._settings, plugin_configuration
                )
                html_export_plugin.export(document)

                convertHTMLToPDF(self._tmp_html_file, pdf_output_file)
        except Exception as e:
            self.cleanup()
            raise e

        self.cleanup()

        self.log("Single page pdf pair report '%s' written" % pdf_output_file)

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [PluginConfigurationKey("output_file", "The PDF output file")] + super(
            PDFExportPairReportPlugin, PDFExportPairReportPlugin
        ).getConfigurationInformation()
