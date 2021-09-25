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
from elf_diff.git import gitRepoInfo
from elf_diff.symbol import Symbol
import progressbar
import sys
import operator
import os
import datetime
from distutils import dir_util
from shutil import copyfile


def getRelpath(html_output_file, target_dir):
    html_dirname = os.path.dirname(html_output_file)
    return os.path.relpath(target_dir, html_dirname)


class HTMLContent(object):
    def __init__(self):
        self.visible = True
        self.have_title = False
        self.keywords = None
        self.content = None
        self.settings = None
        self.single_page = False

    def prepareKeywords(self):
        pass

    def generateContent(self):
        pass

    def getFilename(self):
        pass

    def getRelPathToOverviewFile(self):
        pass

    def getContent(self):
        self.prepareKeywords()
        self.generateContent()
        return self.content

    def getHeaderKeywords(self, html_output_file):
        base_dir = getRelpath(html_output_file, self.settings.html_dir)

        sortable_js_content = f'<script src="{base_dir}/js/sorttable.js"></script>'
        elf_diff_general_css_content = (
            f'<link rel="stylesheet" href="{base_dir}/css/elf_diff_general.css">'
        )

        return {
            "elf_diff_general_css_content": elf_diff_general_css_content,
            "sortable_js_content": sortable_js_content,
        }

    def exportFiles(self, base_keywords):
        self.prepareKeywords()
        self.generateContent()

        html_template_filename = "frame_content.html"

        html_output_file = f"{self.settings.html_dir}/" + self.getFilename()

        keywords = self.keywords or {}

        keywords.update(base_keywords)

        keywords.update(
            {
                "page_title": self.getPageTitle(),
                "have_title": self.have_title,
                "content": self.content,
                "index_file": self.getRelPathToOverviewFile(),
            }
        )

        keywords.update(self.getHeaderKeywords(html_output_file))

        html.configureTemplateWrite(
            self.settings, html_template_filename, html_output_file, keywords
        )


class PersistingSymbol(HTMLContent):
    def __init__(self, old_symbol, new_symbol):
        super().__init__()
        self.old_symbol = old_symbol
        self.new_symbol = new_symbol
        self.header_tag = "H4"

    def prepareKeywords(self):

        if self.keywords is not None:
            return

        size_diff = self.new_symbol.size - self.old_symbol.size

        if self.old_symbol.symbol_type == Symbol.type_data:
            instruction_differences = "Data symbol -> no assembly"
        elif self.old_symbol.__eq__(self.new_symbol):
            instruction_differences = "Instructions unchanged"
        else:
            instruction_differences = self.old_symbol.getDifferencesAsHTML(
                self.new_symbol, "   "
            )

        overview_anchor = f"persisting_symbol_overview_{self.old_symbol.id}"
        details_file = ""
        details_anchor = f"persisting_symbol_details_{self.old_symbol.id}"

        if self.single_page is False:
            details_file = self.getFilename()
            have_return_links = False
            overview_file = self.getRelPathToOverviewFile() + "/index.html"
        else:
            have_return_links = True
            overview_file = ""

        if self.old_symbol.symbol_type == Symbol.type_data:
            have_details_link = False
        else:
            have_details_link = True

        self.keywords = {
            "old_id": str(self.old_symbol.id),
            "new_id": str(self.new_symbol.id),
            "name": self.old_symbol.name,
            "type": self.new_symbol.type,
            "old_size": str(self.old_symbol.size),
            "new_size": str(self.new_symbol.size),
            "size_diff": str(size_diff),
            "size_diff_class": html.highlightNumberClass(size_diff),
            "instruction_differences": instruction_differences,
            "header_tag": self.header_tag,
            "overview_file": overview_file,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
            "have_return_links": have_return_links,
            "have_details_link": have_details_link,
        }

    def generateContent(self):

        if self.content is not None:
            return

        html_template_filename = "persisting_symbol_details_content.html"

        self.content = html.configureTemplate(
            self.settings, html_template_filename, self.keywords
        )

    def getFilename(self):
        return f"details/persisting/{self.old_symbol.id}.html"

    def getPageTitle(self):
        return "Persisting Symbol " + self.keywords["name"]

    def getRelPathToOverviewFile(self):
        if self.single_page is False:
            return "../.."
        return "."


class PersistingSymbolsOverview(HTMLContent):
    def __init__(self, persisting_symbols):
        super().__init__()
        self.persisting_symbols = persisting_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        if len(self.persisting_symbols) == 0:
            self.content = "No persisting symbols"
            return

        html_template_filename = "persisting_symbols_overview_content.html"

        self.overall_size_difference = 0
        self.content = ""

        for persisting_symbol in self.persisting_symbols:
            new_symbol = persisting_symbol.new_symbol
            if new_symbol.livesInProgramMemory():
                old_symbol = persisting_symbol.old_symbol
                self.overall_size_difference += new_symbol.size - old_symbol.size

        if self.single_page is False:
            link_target_frame = 'target="details"'
        else:
            link_target_frame = ""

        symbols_keywords = []

        for persisting_symbol in self.persisting_symbols:
            persisting_symbol.prepareKeywords()
            symbols_keywords.append(persisting_symbol.keywords)

        self.content = html.configureTemplate(
            self.settings,
            html_template_filename,
            {"symbols": symbols_keywords, "link_target_frame": link_target_frame},
        )

        if self.settings.consider_equal_sized_identical:
            self.content += "Equal sized symbols forcefully ignored."

    def getFilename(self):
        return "persisting_symbols_overview.html"

    def getPageTitle(self):
        return "Persisting Symbols Overview"

    def getRelPathToOverviewFile(self):
        return "."


class PersistingSymbolsDetails(HTMLContent):
    def __init__(self, persisting_symbols):
        super().__init__()
        self.persisting_symbols = persisting_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        symbols_listed = False
        html_lines = []

        for persisting_symbol in self.persisting_symbols:

            persisting_symbol.prepareKeywords()

            symbols_listed = True

            if persisting_symbol.keywords["have_details_link"] is False:
                continue

            html_lines.append(persisting_symbol.getContent())

        if not symbols_listed:
            self.content = "No persisting functions or no symbol changes"
            return

        self.content = "\n".join(html_lines)

    def exportFiles(self, base_keywords):
        if self.single_page is True:
            return

        for persisting_symbol in self.persisting_symbols:
            persisting_symbol.exportFiles(base_keywords)


class IsolatedSymbol(HTMLContent):
    def __init__(self, description, symbol):
        super().__init__()
        self.description = description
        self.symbol = symbol
        self.header_tag = "H4"

    def prepareKeywords(self):

        if self.keywords is not None:
            return

        overview_file = ""
        overview_anchor = f"{self.description}_symbol_overview_{self.symbol.id}"
        details_file = ""
        details_anchor = f"{self.description}_symbol_details_{self.symbol.id}"

        if self.single_page is False:
            overview_file = "../../index.html"
            details_file = self.getFilename()
            have_return_links = False
        else:
            have_return_links = True

        if self.symbol.symbol_type == Symbol.type_data:
            have_details_link = False
        else:
            have_details_link = True

        self.keywords = {
            "description": self.description,
            "id": str(self.symbol.id),
            "name": self.symbol.name,
            "type": self.symbol.type,
            "size": str(self.symbol.size),
            "instructions": self.symbol.getInstructionsBlockEscaped(""),
            "header_tag": self.header_tag,
            "overview_file": overview_file,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
            "have_return_links": have_return_links,
            "have_details_link": have_details_link,
        }

    def generateContent(self):

        if self.content is not None:
            return

        html_template_filename = "isolated_symbol_details_content.html"

        self.content = html.configureTemplate(
            self.settings, html_template_filename, self.keywords
        )

    def getFilename(self):
        return f"details/{self.description}/{self.symbol.id}.html"

    def getPageTitle(self):
        return self.description.capitalize() + " Symbol " + self.keywords["name"]

    def getRelPathToOverviewFile(self):
        if self.single_page is False:
            return "../.."
        return "."


class IsolatedSymbolsOverview(HTMLContent):
    def __init__(self, description, isolated_symbols):
        super().__init__()
        self.description = description
        self.isolated_symbols = isolated_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        if len(self.isolated_symbols) == 0:
            self.content = f"No {self.description} symbols"
            return

        html_template_filename = "isolated_symbols_overview_content.html"

        self.overall_symbol_size = 0
        symbols_keywords = []
        for isolated_symbol in self.isolated_symbols:
            isolated_symbol.prepareKeywords()
            symbols_keywords.append(isolated_symbol.keywords)
            self.overall_symbol_size += isolated_symbol.symbol.size

        if self.single_page is False:
            link_target_frame = 'target="details"'
        else:
            link_target_frame = ""

        self.content = html.configureTemplate(
            self.settings,
            html_template_filename,
            {"symbols": symbols_keywords, "link_target_frame": link_target_frame},
        )

    def getFilename(self):
        return f"{self.description}_symbols_overview.html"

    def getPageTitle(self):
        return self.description.capitalize() + " Symbols Overview"

    def getRelPathToOverviewFile(self):
        return "."


class IsolatedSymbolsDetails(HTMLContent):
    def __init__(self, description, isolated_symbols):
        super().__init__()
        self.isolated_symbols = isolated_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        symbols_listed = False
        html_lines = []

        for isolated_symbol in self.isolated_symbols:

            isolated_symbol.prepareKeywords()

            if isolated_symbol.keywords["have_details_link"] is False:
                continue

            symbols_listed = True

            html_lines.append(isolated_symbol.getContent())

        if not symbols_listed:
            self.content = f"No functions {self.description}"
            return

        self.content = "\n".join(html_lines)

    def exportFiles(self, base_keywords):
        if self.single_page is True:
            return

        for isolated_symbol in self.isolated_symbols:
            isolated_symbol.exportFiles(base_keywords)


class SimilarSymbolPair(HTMLContent):
    def __init__(self, symbol_pair, id):
        super().__init__()
        self.symbol_pair = symbol_pair
        self.header_tag = "H4"
        self.id = id

    def prepareKeywords(self):

        if self.keywords is not None:
            return

        old_symbol = self.symbol_pair.old_symbol
        new_symbol = self.symbol_pair.new_symbol

        old_representation = html.diffStringsSource(old_symbol.name, new_symbol.name)
        new_representation = html.diffStringsTarget(old_symbol.name, new_symbol.name)

        instructions_similarity_str = "N/A"
        if self.symbol_pair.instructions_similarity is not None:
            instructions_similarity_str = "{:.1f}".format(
                self.symbol_pair.instructions_similarity * 100.0
            )

        size_diff = new_symbol.size - old_symbol.size

        overview_anchor = f"similar_symbols_overview_{self.id}"
        details_file = ""
        details_anchor = f"similar_symbols_details_{self.id}"

        if self.single_page is False:
            details_file = self.getFilename()
            have_return_links = False
        else:
            have_return_links = True

        if old_symbol.symbol_type == Symbol.type_data:
            have_details_link = False
        else:
            have_details_link = True

        self.keywords = {
            "table_id": str(self.id),
            "old_representation": old_representation,
            "new_representation": new_representation,
            "old_type": old_symbol.type,
            "new_type": new_symbol.type,
            "old_size": str(old_symbol.size),
            "new_size": str(new_symbol.size),
            "size_diff": "%+d" % size_diff,
            "size_diff_class": html.highlightNumberClass(size_diff),
            "signature_similarity": "{:.1f}".format(
                self.symbol_pair.symbol_similarity * 100.0
            ),
            "instruction_similarity": instructions_similarity_str,
            "instruction_differences": old_symbol.getDifferencesAsHTML(
                new_symbol, "   "
            ),
            "header_tag": self.header_tag,
            "overview_anchor": overview_anchor,
            "details_file": details_file,
            "details_anchor": details_anchor,
            "have_return_links": have_return_links,
            "have_details_link": have_details_link,
            "overview_file": self.getRelPathToOverviewFile(),
        }

    def generateContent(self):

        if self.content is not None:
            return

        html_template_filename = "similar_symbols_details_content.html"

        self.content = html.configureTemplate(
            self.settings, html_template_filename, self.keywords
        )

    def getFilename(self):
        return f"details/similar/{self.id}.html"

    def getPageTitle(self):
        return f"Similar Symbol Pair {self.id}"

    def getRelPathToOverviewFile(self):
        if self.single_page is False:
            return "../.."
        return "."


class SimilarSymbolsOverview(HTMLContent):
    def __init__(self, similar_symbols):
        super().__init__()
        self.similar_symbols = similar_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        if len(self.similar_symbols) == 0:
            self.content = "No similar symbols"
            return

        html_template_filename = "similar_symbols_overview_content.html"

        symbols_keywords = []
        for similar_symbol in self.similar_symbols:
            similar_symbol.prepareKeywords()
            symbols_keywords.append(similar_symbol.keywords)

        if self.single_page is False:
            link_target_frame = 'target="details"'
        else:
            link_target_frame = ""

        self.content = html.configureTemplate(
            self.settings,
            html_template_filename,
            {"symbols": symbols_keywords, "link_target_frame": link_target_frame},
        )

    def getFilename(self):
        return "similar_symbols_overview.html"

    def getPageTitle(self):
        return "Similar Symbols Overview"

    def getRelPathToOverviewFile(self):
        return "."


class SimilarSymbolsDetails(HTMLContent):
    def __init__(self, similar_symbols):
        super().__init__()
        self.similar_symbols = similar_symbols
        self.have_title = True

    def generateContent(self):

        if self.content is not None:
            return

        symbols_listed = False
        html_lines = []

        for similar_symbol in self.similar_symbols:

            similar_symbol.prepareKeywords()

            if similar_symbol.keywords["have_details_link"] is False:
                continue

            symbols_listed = True

            html_lines.append(similar_symbol.getContent())

        if not symbols_listed:
            self.content = "No similar symbol pairss"
            return

        self.content = "\n".join(html_lines)

    def exportFiles(self, base_keywords):
        if self.single_page is True:
            return

        for similar_symbol in self.similar_symbols:
            similar_symbol.exportFiles(base_keywords)


class StatisticsOverview(HTMLContent):
    def __init__(self, binary_pair):
        super().__init__()
        self.binary_pair = binary_pair
        self.have_title = True

    def prepareKeywords(self):

        if self.keywords is not None:
            return

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        self.keywords = {
            "old_binary_file": html.escapeString(self.settings.old_alias),
            "new_binary_file": html.escapeString(self.settings.new_alias),
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
        }

    def generateContent(self):

        if self.content is not None:
            return

        html_template_filename = "stats.html"

        self.content = html.configureTemplate(
            self.settings, html_template_filename, self.keywords
        )

    def getFilename(self):
        return "stats.html"

    def getPageTitle(self):
        return "Statistics"

    def getRelPathToOverviewFile(self):
        return "."


class PairReport(Report):
    def __init__(self, settings):

        self.settings = settings
        self.single_page = False

        self.validateSettings()

        self.binary_pair = BinaryPair(
            settings, settings.old_binary_filename, settings.new_binary_filename
        )

        self.is_prepared = False

        self.persisting_symbols_overview = None
        self.persisting_symbols_details = None

        self.disappeared_symbols_overview = None
        self.disappeared_symbols_details = None

        self.new_symbols_overview = None
        self.new_symbols_details = None

        self.statistics_overview = None

        self.base_page_keywords = None

        self.html_contents = []

    def getReportBasename(self):
        return "pair_report"

    def validateSettings(self):
        if not self.settings.old_binary_filename:
            unrecoverableError("No old binary filename defined")

        if not self.settings.new_binary_filename:
            unrecoverableError("No new binary filename defined")

    def prepareHTMLContent(self, html_content):
        html_content.settings = self.settings
        html_content.single_page = self.single_page

    def registerHTMLContent(self, html_content):
        self.prepareHTMLContent(html_content)
        self.html_contents.append(html_content)

    def preparePersistingSymbols(self):

        print("Preparing persisting symbols ...")
        sys.stdout.flush()

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        diff_by_symbol = {}
        for symbol_name in self.binary_pair.persisting_symbol_names:
            old_symbol = old_binary.symbols[symbol_name]
            new_symbol = new_binary.symbols[symbol_name]

            size_difference = new_symbol.size - old_symbol.size

            if (size_difference == 0) and self.settings.consider_equal_sized_identical:
                continue

            diff_by_symbol[symbol_name] = size_difference

        sorted_by_diff = sorted(
            diff_by_symbol.items(), key=operator.itemgetter(1), reverse=True
        )

        persisting_symbols = []
        for i in progressbar.progressbar(range(len(sorted_by_diff))):

            symbol_tuple = sorted_by_diff[i]

            symbol_name = symbol_tuple[0]

            old_symbol = old_binary.symbols[symbol_name]
            new_symbol = new_binary.symbols[symbol_name]

            persisting_symbol = PersistingSymbol(
                old_symbol=old_symbol, new_symbol=new_symbol
            )

            self.prepareHTMLContent(persisting_symbol)

            persisting_symbols.append(persisting_symbol)

        self.persisting_symbols_overview = PersistingSymbolsOverview(
            persisting_symbols=persisting_symbols
        )
        self.registerHTMLContent(self.persisting_symbols_overview)

        self.persisting_symbols_details = PersistingSymbolsDetails(
            persisting_symbols=persisting_symbols
        )
        self.registerHTMLContent(self.persisting_symbols_details)

    def prepareIsolatedSymbols(self, description, binary, symbol_names, symbols):

        print(f"Preparing {description} symbols ...")
        sys.stdout.flush()

        symbol_names_sorted = sorted(
            symbol_names,
            key=lambda symbol_name: symbols[symbol_name].size,
            reverse=True,
        )

        isolated_symbols = []
        for symbol_name in progressbar.progressbar(symbol_names_sorted):
            symbol = binary.symbols[symbol_name]

            isolated_symbol = IsolatedSymbol(description, symbol)
            self.prepareHTMLContent(isolated_symbol)

            isolated_symbols.append(isolated_symbol)

        overview = IsolatedSymbolsOverview(
            description, isolated_symbols=isolated_symbols
        )
        self.registerHTMLContent(overview)

        details = IsolatedSymbolsDetails(description, isolated_symbols=isolated_symbols)
        self.registerHTMLContent(details)

        return overview, details

    def prepareDisappearedSymbols(self):

        (
            self.disappeared_symbols_overview,
            self.disappeared_symbols_details,
        ) = self.prepareIsolatedSymbols(
            description="disappeared",
            binary=self.binary_pair.old_binary,
            symbol_names=self.binary_pair.disappeared_symbol_names,
            symbols=self.binary_pair.old_binary.symbols,
        )

    def prepareNewSymbols(self):

        (
            self.new_symbols_overview,
            self.new_symbols_details,
        ) = self.prepareIsolatedSymbols(
            description="new",
            binary=self.binary_pair.new_binary,
            symbol_names=self.binary_pair.new_symbol_names,
            symbols=self.binary_pair.new_binary.symbols,
        )

    def prepareSimilarSymbols(self):

        print("Preparing similar symbols ...")
        sys.stdout.flush()

        similar_symbols = []
        id = 0
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):

            symbol_pair = self.binary_pair.similar_symbols[i]

            if (
                symbol_pair.old_symbol.size == symbol_pair.new_symbol.size
            ) and self.settings.consider_equal_sized_identical:
                continue

            similar_symbol_pair = SimilarSymbolPair(symbol_pair, id)
            self.prepareHTMLContent(similar_symbol_pair)

            similar_symbols.append(similar_symbol_pair)

            id += 1

        self.similar_symbols_overview = SimilarSymbolsOverview(
            similar_symbols=similar_symbols
        )
        self.registerHTMLContent(self.similar_symbols_overview)

        self.similar_symbols_details = SimilarSymbolsDetails(
            similar_symbols=similar_symbols
        )
        self.registerHTMLContent(self.similar_symbols_details)

    def prepareStatistics(self):
        self.statistics_overview = StatisticsOverview(self.binary_pair)
        self.registerHTMLContent(self.statistics_overview)

    def prepareBasePageKeywords(self):

        if self.settings.project_title:
            doc_title = html.escapeString(self.settings.project_title)
        else:
            doc_title = "ELF Binary Comparison"

        if self.single_page is True:
            home = '<a href="#home">&#x21A9;</a>'
        else:
            home = ""

        self.base_page_keywords = {
            "page_title": "ELF Binary Comparison - (c) 2021 by noseglasses",
            "doc_title": doc_title,
            "elf_diff_repo_base": self.settings.module_path,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elfdiff_git_version": gitRepoInfo(self.settings),
            "home": home,
            "old_binary_file": html.escapeString(self.settings.old_alias),
            "new_binary_file": html.escapeString(self.settings.new_alias),
        }

    def getScriptElements(self, html_output_file=None):

        if html_output_file is None:
            base_dir = self.settings.module_path
        else:
            base_dir = getRelpath(html_output_file, self.settings.html_dir)

        if self.single_page is True:
            (
                sortable_js_content,
                elf_diff_general_css_content,
            ) = self.getSinglePageScriptContent()
        else:
            sortable_js_content = f'<script src="{base_dir}/js/sorttable.js"></script>'
            elf_diff_general_css_content = (
                f'<link rel="stylesheet" href="{base_dir}/css/elf_diff_general.css">'
            )

        return elf_diff_general_css_content, sortable_js_content

    def getMainPageHeaderKeywords(self, html_output_file):

        elf_diff_general_css_content, sortable_js_content = self.getScriptElements(
            html_output_file
        )

        return {
            "elf_diff_general_css_content": elf_diff_general_css_content,
            "sortable_js_content": sortable_js_content,
        }

    def prepare(self):
        if self.is_prepared:
            return

        self.preparePersistingSymbols()
        self.prepareDisappearedSymbols()
        self.prepareNewSymbols()
        self.prepareSimilarSymbols()
        self.prepareStatistics()

        self.prepareBasePageKeywords()

        self.is_prepared = True

    def getBaseTitlePageTemplateKeywords(self, html_output_file=None):

        show_toc_details = False

        if self.settings.build_info == "":
            show_build_info = False
        else:
            show_build_info = True

        show_binary_details = False
        if self.settings.old_binary_info == "":
            show_old_binary_info = False
        else:
            show_old_binary_info = True
            show_binary_details = True

        if self.settings.new_binary_info == "":
            show_new_binary_info = False
        else:
            show_new_binary_info = True
            show_binary_details = True

        template_keywords = {
            "num_persisting_symbols": str(
                len(self.binary_pair.persisting_symbol_names)
            ),
            "num_disappeared_symbols": str(self.binary_pair.num_symbols_disappeared),
            "num_new_symbols": str(self.binary_pair.num_symbols_new),
            "show_old_binary_info": show_old_binary_info,
            "show_new_binary_info": show_new_binary_info,
            "skip_details": self.settings.skip_details,
            "show_toc_details": show_toc_details,
            "show_binary_details": show_binary_details,
            "old_binary_info": html.escapeString(self.settings.old_binary_info),
            "new_binary_info": html.escapeString(self.settings.new_binary_info),
            "show_build_info": show_build_info,
            "build_info": html.escapeString(self.settings.build_info),
        }

        template_keywords.update(self.base_page_keywords)

        return template_keywords

    def getSinglePageTemplateKeywords(self):

        sortable_js_file = self.settings.module_path + "/html/js/sorttable.js"
        sortable_js_content = None
        with open(sortable_js_file, "r", encoding="ISO-8859-1") as file:
            sortable_js_content = "<script>\n%s\n</script>\n" % html.escapeString(
                file.read()
            )

        elf_diff_general_css_file = (
            self.settings.module_path + "/html/css/elf_diff_general.css"
        )
        elf_diff_general_css_content = None
        with open(elf_diff_general_css_file, "r") as file:
            elf_diff_general_css_content = (
                "<style>\n%s\n</style>\n" % html.escapeString(file.read())
            )

        return {
            "persisting_symbols_overview_visible": True,
            "disappeared_symbols_overview_visible": True,
            "new_symbols_overview_visible": True,
            "similar_symbols_overview_visible": True,
            "num_similar_symbols": str(
                len(self.similar_symbols_overview.similar_symbols)
            ),
            "persisting_symbols_overview": self.persisting_symbols_overview.getContent(),
            "disappeared_symbols_overview": self.disappeared_symbols_overview.getContent(),
            "new_symbols_overview": self.new_symbols_overview.getContent(),
            "similar_symbols_overview": self.similar_symbols_overview.getContent(),
            "persisting_symbols_delta": self.persisting_symbols_overview.overall_size_difference,
            "disappeared_symbols_size": self.disappeared_symbols_overview.overall_symbol_size,
            "new_symbols_size": self.new_symbols_overview.overall_symbol_size,
            "elf_diff_general_css_content": elf_diff_general_css_content,
            "sortable_js_content": sortable_js_content,
        }

    def writeSinglePageHTMLReport(self, output_file=None):

        self.prepare()

        html_template_file = "pair_report_single_page.html"

        if self.settings.skip_details:
            persisting_symbol_details_content = ""
            disappeared_symbol_details_content = ""
            new_symbol_details_content = ""
            similar_symbol_details_content = ""
        else:
            persisting_symbol_details_content = (
                self.persisting_symbols_details.getContent()
            )
            disappeared_symbol_details_content = (
                self.disappeared_symbols_details.getContent()
            )
            new_symbol_details_content = self.new_symbols_details.getContent()
            similar_symbol_details_content = self.similar_symbols_details.getContent()

        single_page_keywords = {
            "stats_content": self.statistics_overview.getContent(),
            "persisting_symbols_details_content": persisting_symbol_details_content,
            "disappeared_symbols_details_content": disappeared_symbol_details_content,
            "new_symbols_details_content": new_symbol_details_content,
            "similar_symbols_details_content": similar_symbol_details_content,
        }

        template_keywords = self.getBaseTitlePageTemplateKeywords()
        template_keywords.update(self.getSinglePageTemplateKeywords())

        template_keywords.update(single_page_keywords)

        if output_file is None:
            output_file = self.settings.html_file

        html.configureTemplateWrite(
            self.settings, html_template_file, output_file, template_keywords
        )

    def copyStyleFilesAndScripts(self, source_dir, target_dir):
        dir_util.copy_tree(source_dir, target_dir)

    def writeMultiPageHTMLReport(self):

        self.prepare()

        dirs = [
            self.settings.html_dir,
            self.settings.html_dir + "/details",
            self.settings.html_dir + "/details/persisting",
            self.settings.html_dir + "/details/disappeared",
            self.settings.html_dir + "/details/new",
            self.settings.html_dir + "/details/similar",
            self.settings.html_dir + "/images",
        ]

        for dir in dirs:
            if not os.path.exists(dir):
                os.mkdir(dir)

        html_template_file = "pair_report_index_page.html"

        html_index_filename = f"{self.settings.html_dir}/index.html"

        template_keywords = self.getBaseTitlePageTemplateKeywords(html_index_filename)

        template_keywords[
            "sortable_js_content"
        ] = '<script src="./js/sorttable.js"></script>'
        template_keywords[
            "elf_diff_general_css_content"
        ] = '<link rel="stylesheet" href="./css/elf_diff_general.css">'

        # Don't display the details section in the TOC
        template_keywords["show_toc_details"] = False

        html.configureTemplateWrite(
            self.settings, html_template_file, html_index_filename, template_keywords
        )

        # Generate details pages

        for html_content in self.html_contents:
            html_content.exportFiles(self.base_page_keywords)

        self.copyStyleFilesAndScripts(
            self.settings.module_path + "/html/css", self.settings.html_dir + "/css"
        )
        self.copyStyleFilesAndScripts(
            self.settings.module_path + "/html/js", self.settings.html_dir + "/js"
        )
        copyfile(
            self.settings.module_path + "/images/favicon.png",
            self.settings.html_dir + "/images/favicon.png",
        )
