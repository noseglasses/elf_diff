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
from elf_diff.error_handling import warning
from elf_diff.plugins.export.html.plugin import HTMLExportPairReportPlugin
import tempfile
import os


def convertHTMLToPDF(html_file, pdf_file):
    try:
        from weasyprint import HTML
    except ImportError:
        warning("Unable to import module weasyprint")
        warning("No pdf export supported")
        return

    HTML(html_file).write_pdf(pdf_file)


class PDFExportPairReportPlugin(ExportPairReportPlugin):
    def __init__(self, settings, plugin_configuration):
        super().__init__(settings, plugin_configuration)

    @staticmethod
    def cleanup(filename):
        if os.path.isfile(filename):
            os.remove(filename)

    def export(self, document):

        pdf_output_file = self.getConfigurationParameter("output_file")

        tmp_html_file = os.path.join(
            tempfile._get_default_tempdir(),
            next(tempfile._get_candidate_names()) + ".html",
        )

        try:
            plugin_configuration = {
                "single_page": True,
                "output_file": tmp_html_file,
                "quiet": True,
            }
            html = HTMLExportPairReportPlugin(self.settings, plugin_configuration)
            html.export(document)

            convertHTMLToPDF(tmp_html_file, pdf_output_file)
        except Exception as e:
            PDFExportPairReportPlugin.cleanup(tmp_html_file)
            raise e

        PDFExportPairReportPlugin.cleanup(tmp_html_file)

        self.log("Single page pdf pair report '%s' written" % pdf_output_file)
