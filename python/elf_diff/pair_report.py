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
import elf_diff.html as html
from elf_diff.error_handling import unrecoverableError
from elf_diff.auxiliary import formatMemChange
from elf_diff.git import gitRepoInfo
from elf_diff.symbol import Symbol
import progressbar
import sys
import difflib
import codecs
import operator
import os
import datetime


class PairReport(Report):
    def __init__(self, settings):

        self.settings = settings
        self.single_page = False

        self.validateSettings()

        self.binary_pair = BinaryPair(
            settings, settings.old_binary_filename, settings.new_binary_filename
        )

    def getReportBasename(self):
        return "pair_report"

    def validateSettings(self):
        if not self.settings.old_binary_filename:
            unrecoverableError("No old binary filename defined")

        if not self.settings.new_binary_filename:
            unrecoverableError("No new binary filename defined")

    def persistingSymbolsDetailFilename(self, id):
        return f"details/persisting_symbols/{id}.html"

    def isolatedSymbolsDetailFilename(self, id, description):
        return f"details/{description}_symbols/{id}.html"

    def similarSymbolsDetailFilename(self, id):
        return f"details/similar_symbols/{id}.html"

    def generatePersistingSymbolKeywords(self, old_symbol, new_symbol, header_tag=None):

        size_diff = new_symbol.size - old_symbol.size

        if old_symbol.__eq__(new_symbol):
            instruction_differences = "Instructions unchanged"
        else:
            instruction_differences = old_symbol.getDifferencesAsHTML(new_symbol, "   ")

        if header_tag is None:
            header_tag = self.settings.symbols_html_header

        overview_file = ""
        overview_anchor = f"persisting_symbol_overview_{old_symbol.id}"
        details_file = ""
        details_anchor = f"persisting_symbol_details_{old_symbol.id}"

        if self.single_page == False:
            overview_file = "../../index.html"
            details_file = self.persistingSymbolsDetailFilename(old_symbol.id)

        return {
            "old_id": str(old_symbol.id),
            "new_id": str(new_symbol.id),
            "name": old_symbol.name,
            "type": new_symbol.type,
            "old_size": str(old_symbol.size),
            "new_size": str(new_symbol.size),
            "size_diff": str(size_diff),
            "size_diff_class": html.highlightNumberClass(size_diff),
            "instruction_differences": instruction_differences,
            "header_tag": header_tag,
            "overview_file": overview_file,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
        }

    def generateAllPersistingSymbolsKeywords(self):

        symbols_keywords = []

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        diff_by_symbol = {}
        for symbol_name in self.binary_pair.persisting_symbol_names:
            old_symbol = old_binary.symbols[symbol_name]
            new_symbol = new_binary.symbols[symbol_name]

            size_difference = new_symbol.size - old_symbol.size

            diff_by_symbol[symbol_name] = size_difference

        sorted_by_diff = sorted(
            diff_by_symbol.items(), key=operator.itemgetter(1), reverse=True
        )

        for i in progressbar.progressbar(range(len(sorted_by_diff))):

            symbol_tuple = sorted_by_diff[i]

            symbol_name = symbol_tuple[0]

            old_symbol = old_binary.symbols[symbol_name]
            new_symbol = new_binary.symbols[symbol_name]

            symbols_keywords.append(
                self.generatePersistingSymbolKeywords(old_symbol, new_symbol)
            )

        return symbols_keywords

    def generatePersistingSymbolsOverviewContent(self):

        html_template_filename = "persisting_symbols_overview_content.html"

        overall_size_difference = 0
        content = ""

        for symbol_name in self.binary_pair.persisting_symbol_names:
            new_symbol = self.binary_pair.new_binary.symbols[symbol_name]
            if new_symbol.livesInProgramMemory():
                old_symbol = self.binary_pair.old_binary.symbols[symbol_name]
                overall_size_difference += new_symbol.size - old_symbol.size

        if overall_size_difference == 0:
            return content, overall_size_difference

        print("Rendering persisting symbols HTML table...")
        sys.stdout.flush()

        content = html.configureTemplate(
            self.settings,
            html_template_filename,
            {"symbols": self.generateAllPersistingSymbolsKeywords()},
        )

        return content, overall_size_difference

    def generatePersistingSymbolsOverview(self):

        content = ""
        visible = False
        overall_size_difference = 0

        if len(self.binary_pair.persisting_symbol_names) == 0:
            return table_html, visible, html.highlightNumber(overall_size_difference)

        (
            content,
            overall_size_difference,
        ) = self.generatePersistingSymbolsOverviewContent()

        visible = True

        return content, visible, html.highlightNumber(overall_size_difference)

    def generatePersistingSymbolDetailContent(self, symbol_keywords):

        html_template_filename = "persisting_symbol_details_content.html"

        return html.configureTemplate(
            self.settings, html_template_filename, symbol_keywords
        )

    def generatePersistingSymbolDetailsHTML(self):

        if len(self.binary_pair.persisting_symbol_names) == 0:
            return ""

        symbols_keywords = self.generateAllPersistingSymbolsKeywords()

        symbols_listed = False
        html_lines = []

        print("Rendering persisting symbols details HTML...")
        sys.stdout.flush()
        for symbol_keywords in progressbar.progressbar(symbols_keywords):

            symbols_listed = True

            html_lines.append(
                self.generatePersistingSymbolDetailContent(symbol_keywords)
            )

        if not symbols_listed:
            return "No persisting functions or no symbol changes"

        return "\n".join(html_lines)

    def generatePersistingSymbolDetailsIndividualHTML(self):

        if len(self.binary_pair.persisting_symbol_names) == 0:
            return

        symbols_keywords = self.generateAllPersistingSymbolsKeywords()

        html_template_filename = "details.html"

        print("Rendering persisting symbols details individual HTML files...")
        sys.stdout.flush()
        for symbol_keywords in progressbar.progressbar(symbols_keywords):

            self.generatePersistingSymbolDetailContent(symbol_keywords)

            old_id = symbol_keywords["old_id"]

            html_output_file = (
                f"{self.settings.html_dir}/"
                + self.persistingSymbolsDetailFilename(old_id)
            )

            details = self.generatePersistingSymbolDetailContent(symbol_keywords)

            template_keywords = self.getBasePageKeywords()
            template_keywords.update(
                {
                    "page_title": "Persisting Symbol " + symbol_keywords["name"],
                    "details": details,
                    "index_file": symbol_keywords["overview_file"],
                }
            )

            html.configureTemplateWrite(
                self.settings,
                html_template_filename,
                html_output_file,
                template_keywords,
            )

    def generateIsolatedSymbolKeywords(self, symbol, description, header_tag=None):

        if header_tag is None:
            header_tag = self.settings.symbols_html_header

        overview_file = ""
        overview_anchor = f"{description}_symbol_overview_{symbol.id}"
        details_file = ""
        details_anchor = f"{description}_symbol_details_{symbol.id}"

        if self.single_page == False:
            overview_file = "../../index.html"
            details_file = self.isolatedSymbolsDetailFilename(symbol.id, description)

        return {
            "id": str(symbol.id),
            "name": symbol.name,
            "type": symbol.type,
            "size": str(symbol.size),
            "instructions": symbol.getInstructionsBlockEscaped(""),
            "header_tag": header_tag,
            "overview_file": overview_file,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
        }

    def generateIsolatedSymbolsOverviewContent(
        self, symbol_names, symbols_by_name, description
    ):

        html_template_filename = "isolated_symbols_overview_content.html"

        template_symbols = []
        overal_symbol_size = 0

        print(f"Rendering {description} symbols HTML table...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(symbol_names))):

            symbol_name = symbol_names[i]
            symbol = symbols_by_name[symbol_name]

            template_symbols.append(
                self.generateIsolatedSymbolKeywords(symbol, description)
            )

            overal_symbol_size += symbol.size

        content = html.configureTemplate(
            self.settings, html_template_filename, {"symbols": template_symbols}
        )

        return content, overal_symbol_size

    def generateIsolatedSymbolsOverview(
        self, symbol_names, symbols_by_name, description
    ):

        content = ""
        overal_symbol_size = 0
        visible = False

        if len(symbol_names) == 0:
            return content, visible, overal_symbol_size

        content, overal_symbol_size = self.generateIsolatedSymbolsOverviewContent(
            symbol_names, symbols_by_name, description
        )

        if overal_symbol_size != 0:
            visible = True

        return content, visible, html.highlightNumber(overal_symbol_size)

    def generateIsolatedSymbolDetailContent(self, symbol_keywords):

        html_template_filename = "isolated_symbol_details_content.html"

        return html.configureTemplate(
            self.settings, html_template_filename, symbol_keywords
        )

    def generateIsolatedSymbolDetailsHTML(self, symbol_names, symbols, description):

        if len(symbol_names) == 0:
            return ""

        symbols_listed = False

        html_lines = []

        print(f"Rendering {description} symbols details HTML...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(symbol_names))):
            symbol_name = symbol_names[i]
            symbol = symbols[symbol_name]

            if symbol.symbol_type == Symbol.type_data:
                continue

            symbol_keywords = self.generateIsolatedSymbolKeywords(symbol, description)

            content = self.generateIsolatedSymbolDetailContent(symbol_keywords)

            html_lines.append(content)

            symbols_listed = True

        if not symbols_listed:
            return f"No functions {description}"

        return "\n".join(html_lines)

    def generateIsolatedSymbolDetailsIndividualHTML(
        self, symbol_names, symbols, description
    ):

        if len(symbol_names) == 0:
            return

        html_template_filename = "details.html"

        print(f"Rendering {description} symbols details individual HTML files...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(symbol_names))):
            symbol_name = symbol_names[i]
            symbol = symbols[symbol_name]

            if symbol.symbol_type == Symbol.type_data:
                continue

            symbol_keywords = self.generateIsolatedSymbolKeywords(symbol, description)

            details = self.generateIsolatedSymbolDetailContent(symbol_keywords)

            id = symbol_keywords["id"]

            html_output_file = (
                f"{self.settings.html_dir}/"
                + self.isolatedSymbolsDetailFilename(id, description)
            )

            template_keywords = self.getBasePageKeywords()
            template_keywords.update(
                {
                    "page_title": description.capitalize()
                    + " Symbol "
                    + symbol_keywords["name"],
                    "details": details,
                    "index_file": symbol_keywords["overview_file"],
                }
            )
            html.configureTemplateWrite(
                self.settings,
                html_template_filename,
                html_output_file,
                template_keywords,
            )

    def generateDisappearedSymbolsInfo(self):

        old_binary = self.binary_pair.old_binary

        symbol_names_sorted = sorted(
            self.binary_pair.disappeared_symbol_names,
            key=lambda symbol_name: old_binary.symbols[symbol_name].size,
            reverse=True,
        )

        return symbol_names_sorted, old_binary.symbols, "disappeared"

    def generateDisappearedSymbolsOverviewContent(self):
        (
            symbol_names,
            symbols_by_name,
            description,
        ) = self.generateDisappearedSymbolsInfo()
        return self.generateIsolatedSymbolsOverviewContent(
            symbol_names=symbol_names,
            symbols_by_name=symbols_by_name,
            description=description,
        )

    def generateDisappearedSymbolsOverview(self):
        (
            symbol_names,
            symbols_by_name,
            description,
        ) = self.generateDisappearedSymbolsInfo()
        return self.generateIsolatedSymbolsOverview(
            symbol_names=symbol_names,
            symbols_by_name=symbols_by_name,
            description=description,
        )

    def generateDisappearedSymbolDetailsHTML(self):

        return self.generateIsolatedSymbolDetailsHTML(
            symbol_names=self.binary_pair.disappeared_symbol_names,
            symbols=self.binary_pair.old_binary.symbols,
            description="disappeared",
        )

    def generateDisappearedSymbolDetailsIndividualHTML(self):

        return self.generateIsolatedSymbolDetailsIndividualHTML(
            symbol_names=self.binary_pair.disappeared_symbol_names,
            symbols=self.binary_pair.old_binary.symbols,
            description="disappeared",
        )

    def generateNewSymbolsInfo(self):

        new_binary = self.binary_pair.new_binary

        symbol_names_sorted = sorted(
            self.binary_pair.new_symbol_names,
            key=lambda symbol_name: new_binary.symbols[symbol_name].size,
            reverse=True,
        )

        return symbol_names_sorted, new_binary.symbols, "new"

    def generateNewSymbolsOverviewContent(self):
        symbol_names, symbols_by_name, description = self.generateNewSymbolsInfo()
        return self.generateIsolatedSymbolsOverviewContent(
            symbol_names=symbol_names,
            symbols_by_name=symbols_by_name,
            description=description,
        )

    def generateNewSymbolsOverview(self):
        symbol_names, symbols_by_name, description = self.generateNewSymbolsInfo()
        return self.generateIsolatedSymbolsOverview(
            symbol_names=symbol_names,
            symbols_by_name=symbols_by_name,
            description=description,
        )

    def generateNewSymbolDetailsHTML(self):

        return self.generateIsolatedSymbolDetailsHTML(
            symbol_names=self.binary_pair.new_symbol_names,
            symbols=self.binary_pair.new_binary.symbols,
            description="new",
        )

    def generateNewSymbolDetailsIndividualHTML(self):

        return self.generateIsolatedSymbolDetailsIndividualHTML(
            symbol_names=self.binary_pair.new_symbol_names,
            symbols=self.binary_pair.new_binary.symbols,
            description="new",
        )

    def generateSimilarSymbolsKeywords(self, index, symbol_pair, header_tag=None):

        if header_tag is None:
            header_tag = self.settings.symbols_html_header

        old_symbol = symbol_pair.old_symbol
        new_symbol = symbol_pair.new_symbol

        old_symbol_name = html.escapeString(old_symbol.name)
        new_symbol_name = html.escapeString(new_symbol.name)

        old_representation = html.diffStringsSource(old_symbol.name, new_symbol.name)
        new_representation = html.diffStringsTarget(old_symbol.name, new_symbol.name)

        instructions_similarity_str = "N/A"
        if symbol_pair.instructions_similarity is not None:
            instructions_similarity_str = "{:.1f}".format(
                symbol_pair.instructions_similarity * 100.0
            )

        size_diff = new_symbol.size - old_symbol.size

        overview_file = ""
        overview_anchor = f"similar_symbols_overview_{index}"
        details_file = ""
        details_anchor = f"similar_symbols_details_{index}"

        if self.single_page == False:
            overview_file = "../../index.html"
            details_file = self.similarSymbolsDetailFilename(index)

        return {
            "table_id": str(index),
            "old_representation": old_representation,
            "new_representation": new_representation,
            "old_type": old_symbol.type,
            "new_type": new_symbol.type,
            "old_size": str(old_symbol.size),
            "new_size": str(new_symbol.size),
            "size_diff": str(size_diff),
            "size_diff_class": html.highlightNumberClass(size_diff),
            "signature_similarity": "{:.1f}".format(
                symbol_pair.symbol_similarity * 100.0
            ),
            "instruction_similarity": instructions_similarity_str,
            "instruction_differences": old_symbol.getDifferencesAsHTML(
                new_symbol, "   "
            ),
            "header_tag": header_tag,
            "overview_file": overview_file,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
        }

    def generateSimilarSymbolsOverviewContent(self):

        html_template_filename = "similar_symbols_overview_content.html"
        template_symbols = []

        print("Rendering similar symbols HTML table...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):

            symbol_pair = self.binary_pair.similar_symbols[i]

            template_symbols.append(self.generateSimilarSymbolsKeywords(i, symbol_pair))

        content = html.configureTemplate(
            self.settings, html_template_filename, {"symbols": template_symbols}
        )

        return content

    def generateSimilarSymbolsOverview(self):

        content = ""
        visible = False

        if len(self.binary_pair.similar_symbols) == 0:
            return content, visible, len(self.binary_pair.similar_symbols)

        content = self.generateSimilarSymbolsOverviewContent()

        visible = True

        return content, visible, len(self.binary_pair.similar_symbols)

    def generateSimilarSymbolsDetailsContent(self, symbol_keywords):

        html_template_filename = "similar_symbols_details_content.html"

        return html.configureTemplate(
            self.settings, html_template_filename, symbol_keywords
        )

    def generateSimilarSymbolDetailsHTML(self):

        if len(self.binary_pair.similar_symbols) == 0:
            return ""

        symbols_listed = False

        html_lines = []

        print("Rendering similar symbols details HTML...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
            symbol_pair = self.binary_pair.similar_symbols[i]

            template_keywords = self.generateSimilarSymbolsKeywords(i, symbol_pair)

            html_lines.append(
                self.generateSimilarSymbolsDetailsContent(template_keywords)
            )

            symbols_listed = True

        if not symbols_listed:
            return "No similar functions or no implementation changes"

        return "\n".join(html_lines)

    def generateSimilarSymbolDetailsIndividualHTML(self):

        if len(self.binary_pair.similar_symbols) == 0:
            return ""

        html_template_filename = "details.html"

        print("Rendering similar symbols details individual HTML files...")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
            symbol_pair = self.binary_pair.similar_symbols[i]

            symbol_keywords = self.generateSimilarSymbolsKeywords(i, symbol_pair)

            details = self.generateSimilarSymbolsDetailsContent(symbol_keywords)

            id = symbol_keywords["table_id"]

            html_output_file = (
                f"{self.settings.html_dir}/" + self.similarSymbolsDetailFilename(id)
            )

            template_keywords = self.getBasePageKeywords()
            template_keywords.update(
                {
                    "page_title": "Similar Symbols " + str(id),
                    "details": details,
                    "index_file": symbol_keywords["overview_file"],
                }
            )
            html.configureTemplateWrite(
                self.settings,
                html_template_filename,
                html_output_file,
                template_keywords,
            )

    def getBasePageKeywords(self):

        if self.settings.project_title:
            doc_title = html.escapeString(self.settings.project_title)
        else:
            doc_title = "ELF Binary Comparison"

        return {
            "page_title": "ELF Binary Comparison - (c) 2021 by noseglasses",
            "doc_title": doc_title,
            "elf_diff_repo_base": self.settings.repo_path,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elfdiff_git_version": gitRepoInfo(self.settings),
            "home": '<a href="#home">&#x21A9;</a>',
            "old_binary_file": html.escapeString(self.settings.old_alias),
            "new_binary_file": html.escapeString(self.settings.new_alias),
        }

    def getBaseTitlePageTemplateKeywords(self, skip_details=False):

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        if skip_details:
            details_visibile = False
        else:
            details_visibile = True

        toc_details_visibile = True

        (
            persisting_symbols_overview,
            persisting_symbols_overview_visible,
            persisting_symbols_delta,
        ) = self.generatePersistingSymbolsOverview()
        (
            disappeared_symbols_overview,
            disappeared_symbols_overview_visible,
            disappeared_symbols_size,
        ) = self.generateDisappearedSymbolsOverview()
        (
            new_symbols_overview,
            new_symbols_overview_visible,
            new_symbols_size,
        ) = self.generateNewSymbolsOverview()
        (
            similar_symbols_overview,
            similar_symbols_overview_visible,
            num_similar_symbols,
        ) = self.generateSimilarSymbolsOverview()

        if self.settings.build_info == "":
            build_info_visible = False
        else:
            build_info_visible = True

        binary_details_visible = False
        if self.settings.old_binary_info == "":
            old_binary_info_visible = False
        else:
            old_binary_info_visible = True
            binary_details_visible = True

        if self.settings.new_binary_info == "":
            new_binary_info_visible = False
        else:
            new_binary_info_visible = True
            binary_details_visible = True

        template_keywords = {
            "code_size_old_overall": str(old_binary.progmem_size),
            "code_size_new_overall": str(new_binary.progmem_size),
            "code_size_change_overall": html.highlightNumberDelta(
                old_binary.progmem_size, new_binary.progmem_size
            ),
            "static_ram_old_overall": str(old_binary.static_ram_size),
            "static_ram_new_overall": str(new_binary.static_ram_size),
            "static_ram_change_overall": html.highlightNumberDelta(
                old_binary.static_ram_size, new_binary.static_ram_size
            ),
            "text_size_old_overall": str(old_binary.text_size),
            "text_size_new_overall": str(new_binary.text_size),
            "text_size_change_overall": html.highlightNumberDelta(
                old_binary.text_size, new_binary.text_size
            ),
            "data_size_old_overall": str(old_binary.data_size),
            "data_size_new_overall": str(new_binary.data_size),
            "data_size_change_overall": html.highlightNumberDelta(
                old_binary.data_size, new_binary.data_size
            ),
            "bss_size_old_overall": str(old_binary.bss_size),
            "bss_size_new_overall": str(new_binary.bss_size),
            "bss_size_change_overall": html.highlightNumberDelta(
                old_binary.bss_size, new_binary.bss_size
            ),
            "total_symbols_old": str(len(old_binary.symbols.keys())),
            "total_symbols_new": str(len(new_binary.symbols.keys())),
            "num_persisting_symbols": str(
                len(self.binary_pair.persisting_symbol_names)
            ),
            "num_disappeared_symbols": str(self.binary_pair.num_symbols_disappeared),
            "num_new_symbols": str(self.binary_pair.num_symbols_new),
            "num_similar_symbols": str(num_similar_symbols),
            "persisting_symbols_overview_visible": persisting_symbols_overview_visible,
            "disappeared_symbols_overview_visible": disappeared_symbols_overview_visible,
            "new_symbols_overview_visible": new_symbols_overview_visible,
            "similar_symbols_overview_visible": similar_symbols_overview_visible,
            "persisting_symbols_overview": persisting_symbols_overview,
            "disappeared_symbols_overview": disappeared_symbols_overview,
            "new_symbols_overview": new_symbols_overview,
            "similar_symbols_overview": similar_symbols_overview,
            "persisting_symbols_delta": persisting_symbols_delta,
            "disappeared_symbols_size": disappeared_symbols_size,
            "new_symbols_size": new_symbols_size,
            "old_binary_info_visible": old_binary_info_visible,
            "new_binary_info_visible": new_binary_info_visible,
            "details_visibile": details_visibile,
            "toc_details_visibile": toc_details_visibile,
            "binary_details_visible": binary_details_visible,
            "old_binary_info": html.escapeString(self.settings.old_binary_info),
            "new_binary_info": html.escapeString(self.settings.new_binary_info),
            "build_info_visible": build_info_visible,
            "build_info": html.escapeString(self.settings.build_info),
        }

        template_keywords.update(self.getBasePageKeywords())

        return template_keywords

    def writeSinglePageHTMLReport(self):

        html_template_file = "pair_report_single_page.html"

        template_keywords = self.getBaseTitlePageTemplateKeywords(skip_details)

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        # If we generate a pdf files, we skip the details
        #
        if skip_details:
            persisting_symbol_details_content = ""
            disappeared_symbol_details_content = ""
            new_symbol_details_content = ""
            similar_symbol_details_content = ""
        else:
            persisting_symbol_details_content = (
                self.generatePersistingSymbolDetailsHTML()
            )
            disappeared_symbol_details_content = (
                self.generateDisappearedSymbolDetailsHTML()
            )
            new_symbol_details_content = self.generateNewSymbolDetailsHTML()
            similar_symbol_details_content = self.generateSimilarSymbolDetailsHTML()

        single_page_keywords = {
            "persisting_symbols_details_content": persisting_symbol_details_content,
            "disappeared_symbols_details_content": disappeared_symbol_details_content,
            "new_symbols_details_content": new_symbol_details_content,
            "similar_symbols_details_content": similar_symbol_details_content,
        }

        template_keywords.update(single_page_keywords)

        html.configureTemplateWrite(
            self.settings,
            html_template_file,
            self.settings.html_file,
            template_keywords,
        )

    def writeMultiPageHTMLReport(self):

        dirs = [
            self.settings.html_dir,
            self.settings.html_dir + "/details",
            self.settings.html_dir + "/details/persisting_symbols",
            self.settings.html_dir + "/details/disappeared_symbols",
            self.settings.html_dir + "/details/new_symbols",
            self.settings.html_dir + "/details/similar_symbols",
        ]

        for dir in dirs:
            if not os.path.exists(dir):
                os.mkdir(dir)

        html_template_file = "pair_report_base_index_page.html"

        template_keywords = self.getBaseTitlePageTemplateKeywords()

        # Don't display the details section in the TOC
        template_keywords["toc_details_visible"] = False

        html_index_filename = f"{self.settings.html_dir}/index.html"

        html.configureTemplateWrite(
            self.settings, html_template_file, html_index_filename, template_keywords
        )

        # Generate details pages
        self.generatePersistingSymbolDetailsIndividualHTML()
        self.generateDisappearedSymbolDetailsIndividualHTML()
        self.generateNewSymbolDetailsIndividualHTML()
        self.generateSimilarSymbolDetailsIndividualHTML()


def generatePairReport(settings):
    PairReport(settings).generate()
