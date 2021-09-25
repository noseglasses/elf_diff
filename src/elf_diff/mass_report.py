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

from elf_diff.report import Report
from elf_diff.binary_pair import BinaryPair
from elf_diff.error_handling import unrecoverableError
import elf_diff.html as html
from elf_diff.git import gitRepoInfo


class MassReport(Report):

    html_template_file = "mass_report_template.html"

    def __init__(self, settings):

        self.settings = settings

        if len(self.settings.mass_report_members) == 0:
            unrecoverableError(
                "No mass report binary_pairs members defined in driver file"
            )

        self.generatePairReports()

    def getReportBasename(self):
        return "mass_report"

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
                    code_size_delta_overall=html.highlightNumberDelta(
                        binary_pair.old_binary.progmem_size,
                        binary_pair.new_binary.progmem_size,
                    ),
                    static_ram_old_overall=binary_pair.old_binary.static_ram_size,
                    static_ram_new_overall=binary_pair.new_binary.static_ram_size,
                    static_ram_change_overall=html.highlightNumberDelta(
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
                     <td>{num_new_symbols}</td>
                   </tr>
                """.format(
                    short_name=binary_pair.short_name,
                    num_persisting_symbols=str(
                        len(binary_pair.persisting_symbol_names)
                    ),
                    num_disappeared_symbols=str(binary_pair.num_symbols_disappeared),
                    num_new_symbols=str(binary_pair.num_symbols_new),
                )
            )

        return "\n".join(table_lines_html)

    def configureJinjaKeywords(self, skip_details):

        import datetime

        resource_consumtption_table = self.generateResourceConsumptionTableHTML()
        symbols_table = self.generateSymbolsTableHTML()

        if self.settings.project_title:
            doc_title = html.escapeString(self.settings.project_title)
        else:
            doc_title = "ELF Binary Comparison - Mass Report"

        (
            sortable_js_content,
            elf_diff_general_css_content,
        ) = self.getSinglePageScriptContent()

        return {
            "elf_diff_repo_base": self.settings.module_path,
            "doc_title": doc_title,
            "page_title": u"ELF Binary Comparison - (c) 2019 by noseglasses",
            "resource_consumption_table": resource_consumtption_table,
            "symbols_table": symbols_table,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elfdiff_git_version": gitRepoInfo(self.settings),
            "sortable_js_content": sortable_js_content,
            "elf_diff_general_css_content": elf_diff_general_css_content,
        }

    def getHTMLTemplate(self):
        return MassReport.html_template_file

    def generate(self, html_output_file):
        template_keywords = self.configureJinjaKeywords(self.settings.skip_details)

        html.configureTemplateWrite(
            self.settings,
            MassReport.html_template_file,
            html_output_file,
            template_keywords,
        )
