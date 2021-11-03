# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
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

from elf_diff.binary_pair import BinaryPair
from elf_diff.error_handling import unrecoverableError, warning
from elf_diff.jinja import Configurator
from elf_diff.git import gitRepoInfo
from elf_diff.auxiliary import getDirectoryThatStoresModule, deprecationWarning
import os
import datetime
import tempfile


def convertHTMLToPDF(html_file, pdf_file):
    try:
        from weasyprint import HTML
    except ImportError:
        warning("Unable to import module weasyprint")
        warning("No pdf export supported")
        return

    HTML(html_file).write_pdf(pdf_file)


def highlightNumberClass(number):
    if number > 0:
        return "deterioration"
    elif number < 0:
        return "improvement"

    return "unchanged"


def highlightNumber(number):
    css_class = highlightNumberClass(number)

    if number == 0:
        return '<span class="%s number">%d</span>' % (css_class, number)

    return '<span class="%s number">%+d</span>' % (css_class, number)


def highlightNumberDelta(old_size, new_size):
    return highlightNumber(new_size - old_size)


class MassReport(object):

    html_template_file = "mass_report_template.html"

    def __init__(self, settings):
        """Initialize mass report object."""
        self.settings = settings

        if len(self.settings.mass_report_members) == 0:
            unrecoverableError(
                "No mass report binary_pairs members defined in driver file"
            )

        self.generatePairReports()

    def generatePairReports(self):

        self.binary_pairs = []

        for pair_report_setting in self.settings.mass_report_members:

            binary_pair = BinaryPair(
                self.settings,
                pair_report_setting.old_binary_filename,
                pair_report_setting.new_binary_filename,
            )

            binary_pair.short_name = pair_report_setting.short_name

            self.binary_pairs.append(binary_pair)

    def generateResourceConsumptionTableHTML(self):

        table_lines_html = []

        for binary_pair in self.binary_pairs:

            table_lines_html.append(
                """<tr>
                     <td>{short_name}</td>
                     <td>{code_size_old_overall}</td>
                     <td>{code_size_new_overall}</td>
                     <td>{code_size_delta_overall}</td>
                     <td>{static_ram_old_overall}</td>
                     <td>{static_ram_new_overall}</td>
                     <td>{static_ram_change_overall}</td>
                   </tr>
                """.format(
                    short_name=binary_pair.short_name,
                    code_size_old_overall=binary_pair.old_binary.progmem_size,
                    code_size_new_overall=binary_pair.new_binary.progmem_size,
                    code_size_delta_overall=highlightNumberDelta(
                        binary_pair.old_binary.progmem_size,
                        binary_pair.new_binary.progmem_size,
                    ),
                    static_ram_old_overall=binary_pair.old_binary.static_ram_size,
                    static_ram_new_overall=binary_pair.new_binary.static_ram_size,
                    static_ram_change_overall=highlightNumberDelta(
                        binary_pair.old_binary.static_ram_size,
                        binary_pair.new_binary.static_ram_size,
                    ),
                )
            )

        return "\n".join(table_lines_html)

    def generateSymbolsTableHTML(self):

        table_lines_html = []

        for binary_pair in self.binary_pairs:

            table_lines_html.append(
                """<tr>
                     <td>{short_name}</td>
                     <td>{num_persisting_symbols}</td>
                     <td>{num_disappeared_symbols}</td>
                     <td>{num_appeared_symbols}</td>
                   </tr>
                """.format(
                    short_name=binary_pair.short_name,
                    num_persisting_symbols=str(
                        len(binary_pair.persisting_symbol_names)
                    ),
                    num_disappeared_symbols=str(binary_pair.num_symbols_disappeared),
                    num_appeared_symbols=str(binary_pair.num_symbols_appeared),
                )
            )

        return "\n".join(table_lines_html)

    def configureJinjaKeywords(self, skip_details):

        resource_consumtption_table = self.generateResourceConsumptionTableHTML()
        symbols_table = self.generateSymbolsTableHTML()

        if self.settings.project_title:
            doc_title = self.settings.project_title
        else:
            doc_title = "ELF Binary Comparison - Mass Report"

        return {
            "elf_diff_repo_base": self.settings.module_path,
            "doc_title": doc_title,
            "page_title": u"ELF Binary Comparison - (c) 2019 by noseglasses",
            "resource_consumption_table": resource_consumtption_table,
            "symbols_table": symbols_table,
            "generation_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elf_diff_version": gitRepoInfo(self.settings),
        }

    def generate(self, html_output_file):
        template_keywords = self.configureJinjaKeywords(self.settings.skip_details)

        jinja_template_directory = os.path.join(
            getDirectoryThatStoresModule(self), "j2"
        )

        configurator = Configurator(self.settings, jinja_template_directory)
        configurator.configureTemplateWrite(
            MassReport.html_template_file,
            html_output_file,
            template_keywords,
        )


def writeMassReport(settings):

    deprecationWarning("mass reports")

    mass_report = MassReport(settings)
    mass_report.single_page = True

    if settings.html_file:
        mass_report.generate(settings.html_file)
        print("Single page html mass report '" + settings.html_file + "' written")

    if settings.pdf_file:

        tmp_html_file = os.path.join(
            tempfile._get_default_tempdir(),
            next(tempfile._get_candidate_names()) + ".html",
        )

        mass_report.generate(tmp_html_file)

        print("Temp report: " + tmp_html_file)

        convertHTMLToPDF(tmp_html_file, settings.pdf_file)

        os.remove(tmp_html_file)

        print("Single page pdf mass report '" + settings.pdf_file + "' written")
