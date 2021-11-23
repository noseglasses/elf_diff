# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
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

from elf_diff.binary_pair import BinaryPair
from elf_diff.error_handling import warning
from elf_diff.jinja import Configurator
from elf_diff.git import gitRepoInfo
from elf_diff.auxiliary import getDirectoryThatStoresModuleOfObj, deprecationWarning
from elf_diff.settings import Settings
import os
import datetime
import tempfile
from typing import List, Dict, Optional


def convertHTMLToPDF(html_file: str, pdf_file: str) -> None:
    try:
        from weasyprint import HTML  # type: ignore # Make mypy ignore this module
    except ImportError:
        warning("Unable to import module weasyprint")
        warning("No pdf export supported")
        return

    HTML(html_file).write_pdf(pdf_file)


def cssNumberClassOf(number: int) -> str:
    if number > 0:
        return "deterioration"
    elif number < 0:
        return "improvement"

    return "unchanged"


def highlightNumber(number: int) -> str:
    css_class: str = cssNumberClassOf(number)

    if number == 0:
        return '<span class="%s number">%d</span>' % (css_class, number)

    return '<span class="%s number">%+d</span>' % (css_class, number)


def highlightNumberDelta(old_size: int, new_size: int) -> str:
    return highlightNumber(new_size - old_size)


class MassReport(object):

    HTML_TEMLATE_FILE = "mass_report_template.html"

    def __init__(self, settings: Settings):
        """Initialize mass report object."""
        self.settings: Settings = settings

        if len(self.settings.mass_report_members) == 0:
            raise Exception(
                "No mass report binary_pairs members defined in driver file"
            )

        self.generatePairReports()

    def generatePairReports(self) -> None:

        self.binary_pairs: List[BinaryPair] = []

        for binary_pair_settings in self.settings.mass_report_members:
            binary_pair = BinaryPair(
                settings=self.settings, pair_settings=binary_pair_settings
            )

            self.binary_pairs.append(binary_pair)

    def generateResourceConsumptionTableHTML(self) -> str:

        table_lines_html: List[str] = []

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
                    short_name=binary_pair.pair_settings.short_name,
                    code_size_old_overall=binary_pair.old_binary.symbol_sizes.progmem_size,
                    code_size_new_overall=binary_pair.new_binary.symbol_sizes.progmem_size,
                    code_size_delta_overall=highlightNumberDelta(
                        binary_pair.old_binary.symbol_sizes.progmem_size,
                        binary_pair.new_binary.symbol_sizes.progmem_size,
                    ),
                    static_ram_old_overall=binary_pair.old_binary.symbol_sizes.static_ram_size,
                    static_ram_new_overall=binary_pair.new_binary.symbol_sizes.static_ram_size,
                    static_ram_change_overall=highlightNumberDelta(
                        binary_pair.old_binary.symbol_sizes.static_ram_size,
                        binary_pair.new_binary.symbol_sizes.static_ram_size,
                    ),
                )
            )

        return "\n".join(table_lines_html)

    def generateSymbolsTableHTML(self) -> str:

        table_lines_html: List[str] = []

        for binary_pair in self.binary_pairs:

            table_lines_html.append(
                """<tr>
                     <td>{short_name}</td>
                     <td>{num_persisting_symbols}</td>
                     <td>{num_disappeared_symbols}</td>
                     <td>{num_appeared_symbols}</td>
                   </tr>
                """.format(
                    short_name=binary_pair.pair_settings.short_name,
                    num_persisting_symbols=str(
                        len(binary_pair.persisting_symbol_names)
                    ),
                    num_disappeared_symbols=str(binary_pair.num_symbols_disappeared),
                    num_appeared_symbols=str(binary_pair.num_symbols_appeared),
                )
            )

        return "\n".join(table_lines_html)

    def configureJinjaKeywords(self, skip_details):

        resource_consumtption_table: str = self.generateResourceConsumptionTableHTML()
        symbols_table: str = self.generateSymbolsTableHTML()

        doc_title: str
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

    def generate(self, html_output_file: str) -> None:
        template_keywords: Dict[str, str] = self.configureJinjaKeywords(
            self.settings.skip_details
        )

        jinja_template_directory: str = os.path.join(
            getDirectoryThatStoresModuleOfObj(self), "j2"
        )

        configurator = Configurator(self.settings, jinja_template_directory)
        configurator.configureTemplateWrite(
            MassReport.HTML_TEMLATE_FILE,
            html_output_file,
            template_keywords,
        )


def writeMassReport(settings: Settings) -> None:

    deprecationWarning("mass reports")

    mass_report = MassReport(settings)

    if settings.html_file:
        mass_report.generate(settings.html_file)
        print("Single page html mass report '" + settings.html_file + "' written")

    if settings.pdf_file:
        tmp_html_file: Optional[str] = None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_html_file = os.path.join(tmp, "tmp_html_file.html")

                mass_report.generate(tmp_html_file)

                print("Temp report: " + tmp_html_file)

                convertHTMLToPDF(tmp_html_file, settings.pdf_file)

                os.remove(tmp_html_file)
                tmp_html_file = None
        except Exception as e:
            if tmp_html_file is not None:
                os.remove(tmp_html_file)
            raise e

        if tmp_html_file is not None:
            os.remove(tmp_html_file)

        print("Single page pdf mass report '" + settings.pdf_file + "' written")
