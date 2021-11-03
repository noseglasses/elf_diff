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
from elf_diff.plugin import ExportPairReportPlugin
from elf_diff.binary_pair import BinaryPair
from elf_diff.jinja import Configurator
from elf_diff.symbol import Symbol
import os
from distutils import dir_util
from shutil import copyfile
import difflib


def getRelpath(html_output_file, target_dir):
    html_dirname = os.path.dirname(html_output_file)
    return os.path.relpath(target_dir, html_dirname)


def copyStyleFilesAndScripts(source_dir, target_dir):
    dir_util.copy_tree(source_dir, target_dir)


def getDifferencesAsHTML(old_symbol, new_symbol):
    if old_symbol.type == Symbol.type_data:
        return "Data symbol -> no assembly"
    elif old_symbol.instructions == new_symbol.instructions:
        return "Instructions unchanged"

    diff_class = difflib.HtmlDiff(tabsize=3, wrapcolumn=200)

    old_instruction_lines = old_symbol.instructions.split("\n")
    new_instruction_lines = new_symbol.instructions.split("\n")

    diff_table = diff_class.make_table(
        old_instruction_lines,
        new_instruction_lines,
        fromdesc="Old",
        todesc="New",
        context=True,
        numlines=1000,
    )

    return postHighlightSourceCode(diff_table)


def postHighlightSourceCode(src):
    return src.replace("__ED_SOURCE_START__", '<span class="source">').replace(
        "__ED_SOURCE_END__", "</span>"
    )


class HTMLContent(object):
    def __init__(self):
        """Initializes HTMLContent."""
        self.keywords = None
        self.content = None
        self.infrastructure = None
        self.single_page = False

    def prepareKeywords(self):
        pass

    def generateContent(self):
        pass

    def getFilename(self):  # pylint: disable=no-self-use
        pass

    def getRelPathToOverviewFile(self):
        pass

    def getContent(self):
        self.prepareKeywords()
        self.generateContent()
        return self.content

    def exportFiles(self, jinja_configurator):
        self.prepareKeywords()
        self.generateContent()

        html_template_filename = "frame_content.html"

        html_output_file = os.path.join(
            self.infrastructure.settings.html_dir, self.getFilename()
        )

        keywords = self.infrastructure.getCommonJinjaKeywords()

        keywords.update(
            {
                "page_title": self.getPageTitle(),
                "content": self.content,
                "rel_path_to_index_file": self.getRelPathToOverviewFile(),
            }
        )

        jinja_configurator.configureTemplateWrite(
            html_template_filename, html_output_file, keywords
        )


class SymbolProperties(object):
    def __init__(
        self,
        class_,
        id_getter,
        name_getter,
        additional_overview_content=None,
        joint_symbol_class_getter=None,
        update_entity_keywords=None,
    ):
        self.class_ = class_
        self.id_getter = id_getter
        self.name_getter = name_getter
        self.additional_overview_content = additional_overview_content
        self.joint_symbol_class_getter = joint_symbol_class_getter or (
            lambda symbol_properties: symbol_properties.class_
        )
        self.update_entity_keywords = update_entity_keywords or (
            lambda symbol, keywords: None
        )


class Infrastructure(object):
    def __init__(self, settings, document, jinja_configurator):
        self.settings = settings
        self.document = document
        self.jinja_configurator = jinja_configurator
        self.single_page = False

    def getCommonJinjaKeywords(self):
        return {"is_single_page_report": self.single_page, "document": self.document}


class SymbolEntity(HTMLContent):
    def __init__(self, symbol_of_class, symbol_properties, infrastructure):
        super().__init__()
        self.symbol_of_class = symbol_of_class
        self.symbol_properties = symbol_properties
        self.infrastructure = infrastructure

        actual_symbol_class = symbol_properties.joint_symbol_class_getter(
            symbol_properties
        )
        self.html_template_filename = f"{actual_symbol_class}_symbol_details.html"

    def prepareKeywords(self):
        if self.keywords is None:
            self.keywords = self.infrastructure.getCommonJinjaKeywords()
            self.keywords.update(
                {
                    "symbol": self.symbol_of_class,
                    "symbol_class": self.symbol_properties.class_,
                }
            )
            self.symbol_properties.update_entity_keywords(
                self.symbol_of_class, self.keywords
            )

    def getFilename(self):
        symbol_id = self.symbol_properties.id_getter(
            self.symbol_of_class
        )  # type(self) is necessary as there is some strange behavior class variable lambdas
        return os.path.join(
            "details", self.symbol_properties.class_, "%s.html" % symbol_id
        )

    def getPageTitle(self):
        symbol_name = self.symbol_properties.name_getter(
            self.symbol_of_class
        )  # type(self) is necessary as there is some strange behavior class variable lambdas
        return "%s Symbol %s" % (
            self.symbol_properties.class_.capitalize(),
            symbol_name,
        )

    def generateContent(self):
        self.prepareKeywords()

        if self.content is not None:
            return

        self.content = self.infrastructure.jinja_configurator.configureTemplate(
            self.html_template_filename, self.keywords
        )

    def getRelPathToOverviewFile(self):
        if self.single_page is False:
            return os.path.join("..", "..")
        return "."


class SymbolOverview(HTMLContent):
    def __init__(self, symbol_properties, infrastructure):
        """Initialize the similar symbols overview class."""
        super().__init__()
        self.symbol_properties = symbol_properties
        self.infrastructure = infrastructure

        actual_symbol_class = symbol_properties.joint_symbol_class_getter(
            symbol_properties
        )
        self.html_template_filename = f"{actual_symbol_class}_symbol_overview.html"

    def generateContent(self):

        symbol_class = self.symbol_properties.class_

        symbols_of_class = getattr(self.infrastructure.document.symbols, symbol_class)
        if len(symbols_of_class) == 0:
            return f"No {symbol_class} symbols"

        keywords = self.infrastructure.getCommonJinjaKeywords()
        keywords.update(
            {"symbols": symbols_of_class.values(), "symbol_class": symbol_class}
        )
        self.content = self.infrastructure.jinja_configurator.configureTemplate(
            self.html_template_filename, keywords
        )

        if self.symbol_properties.additional_overview_content is not None:
            self.content += self.symbol_properties.additional_overview_content

    def getFilename(self):  # pylint: disable=no-self-use
        return f"{self.symbol_properties.class_}_symbols_overview.html"

    def getPageTitle(self):  # pylint: disable=no-self-use
        return "%s Symbols Overview" % self.symbol_properties.class_.capitalize()

    def getRelPathToOverviewFile(self):
        return "."


class SymbolDetails(HTMLContent):
    def __init__(self, symbol_properties, infrastructure):
        """Initialize the persisting symbols details class."""
        super().__init__()
        self.symbol_properties = symbol_properties
        self.infrastructure = infrastructure

    def generateContent(self):
        if self.content is not None:
            return

        symbols_of_class = getattr(
            self.infrastructure.document.symbols, self.symbol_properties.class_
        )

        symbols_listed = False
        html_lines = []

        for symbol_of_class in symbols_of_class.values():

            symbols_listed = True

            if symbol_of_class.display_info.display_symbol_details is False:
                continue

            symbol_entity = SymbolEntity(
                symbol_of_class=symbol_of_class,
                symbol_properties=self.symbol_properties,
                infrastructure=self.infrastructure,
            )
            symbol_entity.generateContent()

            html_lines.append(symbol_entity.getContent())

        if not symbols_listed:
            self.content = (
                f"No {self.symbol_properties.class_} functions or no symbol changes"
            )
            return

        self.content = "\n".join(html_lines)

    def exportFiles(self, jinja_configurator):
        if self.infrastructure.single_page is True:
            return

        symbol_class = self.symbol_properties.class_
        symbols_of_class = getattr(self.infrastructure.document.symbols, symbol_class)

        for symbol_of_class in symbols_of_class.values():
            if symbol_of_class.display_info.display_symbol_details is False:
                continue
            symbol_entity = SymbolEntity(
                symbol_of_class=symbol_of_class,
                symbol_properties=self.symbol_properties,
                infrastructure=self.infrastructure,
            )

            symbol_entity.generateContent()
            symbol_entity.exportFiles(jinja_configurator)


class StatisticsOverview(HTMLContent):
    def __init__(self, infrastructure):
        """Initialize the statistics overview class."""
        super().__init__()
        self.infrastructure = infrastructure

    def prepareKeywords(self):
        if self.keywords is not None:
            return

        self.keywords = self.infrastructure.getCommonJinjaKeywords()

    def generateContent(self):

        if self.content is not None:
            return

        html_template_filename = "statistics.html"

        self.content = self.infrastructure.jinja_configurator.configureTemplate(
            html_template_filename, self.keywords
        )

    def getFilename(self):  # pylint: disable=no-self-use
        return "stats.html"

    def getPageTitle(self):  # pylint: disable=no-self-use
        return "Statistics"

    def getRelPathToOverviewFile(self):
        return "."


class DocumentPage(HTMLContent):
    """A HTML document page that contains the document tree"""

    def __init__(self, infrastructure):
        """Initialize the document page class."""
        super().__init__()
        self.infrastructure = infrastructure

    def prepareKeywords(self):
        if self.keywords is not None:
            return

        self.keywords = self.infrastructure.getCommonJinjaKeywords()

    def generateContent(self):
        if self.content is not None:
            return

        html_template_filename = "document.html"

        self.content = self.infrastructure.jinja_configurator.configureTemplate(
            html_template_filename, self.keywords
        )

    def getFilename(self):  # pylint: disable=no-self-use
        return "document.html"

    def getPageTitle(self):  # pylint: disable=no-self-use
        return "Document"

    def getRelPathToOverviewFile(self):
        return "."


class HTMLExportPairReportPlugin(ExportPairReportPlugin):
    symbol_classes = ["persisting", "appeared", "disappeared", "similar"]
    information_types = ["overview", "detail"]

    def __init__(self, settings, plugin_configuration):
        """Initialize the pair report class."""
        super().__init__(settings, plugin_configuration)

        self.settings = settings

        self.binary_pair = BinaryPair(
            settings, settings.old_binary_filename, settings.new_binary_filename
        )

        self.symbol_overviews = {}
        self.symbol_details = {}

        for symbol_class in self.symbol_classes:
            self.symbol_overviews[symbol_class] = None
            self.symbol_details[symbol_class] = None

        self.statistics_overview = None
        self.document_page = None

        self.html_contents = []

        self.is_prepared = False

        self.plugin_configuration = plugin_configuration

        jinja_template_dir = os.path.join(self.getPluginLocation(), "j2")
        self.jinja_configurator = Configurator(self.settings, jinja_template_dir)

    def export(self, document):

        self.infrastructure = Infrastructure(
            settings=self.settings,
            document=document,
            jinja_configurator=self.jinja_configurator,
        )
        self.single_page = self.getConfigurationParameter("single_page")
        self.infrastructure.single_page = self.single_page

        if self.single_page:
            self.exportSinglePage()
        else:
            self.exportMultiPage()

    def registerHTMLContent(self, html_content):
        html_content.settings = self.infrastructure.settings
        html_content.single_page = self.single_page
        self.html_contents.append(html_content)

    def prepareSymbols(self, symbol_properties):
        symbol_overview = SymbolOverview(
            symbol_properties=symbol_properties, infrastructure=self.infrastructure
        )
        self.registerHTMLContent(symbol_overview)
        self.symbol_overviews[symbol_properties.class_] = symbol_overview

        symbol_details = SymbolDetails(
            symbol_properties, infrastructure=self.infrastructure
        )
        self.registerHTMLContent(symbol_details)
        self.symbol_details[symbol_properties.class_] = symbol_details

    def preparePersistingSymbols(self):
        additional_overview_content = None
        if self.infrastructure.settings.consider_equal_sized_identical:
            additional_overview_content = "Equal sized symbols forcefully ignored."

        symbol_properties = SymbolProperties(
            class_="persisting",
            id_getter=lambda symbol: symbol.related_symbols.old.id,
            name_getter=lambda symbol: symbol.related_symbols.old.name,
            additional_overview_content=additional_overview_content,
            update_entity_keywords=lambda symbol, keywords: keywords.update(
                {
                    "instruction_differences_html": getDifferencesAsHTML(
                        symbol.related_symbols.old, symbol.related_symbols.new
                    )
                }
            ),
        )
        self.prepareSymbols(symbol_properties)

    def prepareIsolatedSymbols(self, symbol_class):
        symbol_properties = SymbolProperties(
            class_=symbol_class,
            id_getter=lambda symbol: symbol.actual.id,
            name_getter=lambda symbol: symbol.actual.name,
            joint_symbol_class_getter=lambda _: "isolated",
        )
        self.prepareSymbols(symbol_properties)

    def prepareDisappearedSymbols(self):
        self.prepareIsolatedSymbols(symbol_class="disappeared")

    def prepareAppearedSymbols(self):
        self.prepareIsolatedSymbols(symbol_class="appeared")

    def prepareSimilarSymbols(self):
        symbol_properties = SymbolProperties(
            class_="similar",
            id_getter=lambda symbol: symbol.id,
            name_getter=lambda symbol: symbol.id,  # Similar symbols use the id also as name
            update_entity_keywords=lambda symbol, keywords: keywords.update(
                {
                    "instruction_differences_html": getDifferencesAsHTML(
                        symbol.related_symbols.old, symbol.related_symbols.new
                    )
                }
            ),
        )
        self.prepareSymbols(symbol_properties)

    def getDifferencesAsHTML(self, other, indent):
        diff_class = difflib.HtmlDiff(tabsize=3, wrapcolumn=200)

        diff_table = diff_class.make_table(
            self.instruction_lines,
            other.instruction_lines,
            fromdesc="Old",
            todesc="New",
            context=True,
            numlines=1000,
        )

        return postHighlightSourceCode(diff_table)

    def prepareStatistics(self):
        self.statistics_overview = StatisticsOverview(self.infrastructure)
        self.registerHTMLContent(self.statistics_overview)

    def prepareDocumentPage(self):
        self.document_page = DocumentPage(self.infrastructure)
        self.registerHTMLContent(self.document_page)

    def prepare(self):
        if self.is_prepared:
            return

        self.prepareStatistics()
        self.prepareDocumentPage()

        self.preparePersistingSymbols()
        self.prepareDisappearedSymbols()
        self.prepareAppearedSymbols()

        if not self.infrastructure.settings.skip_symbol_similarities:
            self.prepareSimilarSymbols()

        self.is_prepared = True

    def exportSinglePage(self):

        output_file = self.getConfigurationParameter("output_file")

        self.prepare()

        template_filename = "pair_report_single_page.html"

        template_keywords = self.infrastructure.getCommonJinjaKeywords()

        # Setup jinja keywords for overview/details of persisting, appeared, disappeared and similar symbols
        for information_type in self.information_types:
            information_representations = getattr(self, f"symbol_{information_type}s")
            for symbol_class in self.symbol_classes:
                information_representation = information_representations[symbol_class]
                content = ""
                if information_representation is not None:
                    content = information_representation.getContent()
                template_keywords[f"{symbol_class}_symbol_{information_type}"] = content

        template_keywords.update(
            {
                "statistics": self.statistics_overview.getContent(),
                "skip_symbol_similarities": self.infrastructure.settings.skip_symbol_similarities,
            }
        )

        self.infrastructure.jinja_configurator.configureTemplateWrite(
            template_filename=template_filename,
            output_filename=output_file,
            template_keywords=template_keywords,
        )

        self.log(f"Single page html pair report written to directory '{output_file}'")

    def exportMultiPage(self):

        output_dir = self.getConfigurationParameter("output_dir")

        self.prepare()

        dirs = [
            output_dir,
            os.path.join(output_dir, "details"),
            os.path.join(output_dir, "details", "persisting"),
            os.path.join(output_dir, "details", "disappeared"),
            os.path.join(output_dir, "details", "appeared"),
            os.path.join(output_dir, "details", "similar"),
            os.path.join(output_dir, "images"),
        ]

        for dir_ in dirs:
            if not os.path.exists(dir_):
                os.mkdir(dir_)

        plugin_location = self.getPluginLocation()

        copyStyleFilesAndScripts(
            os.path.join(plugin_location, "j2", "css"),
            os.path.join(output_dir, "css"),
        )
        copyStyleFilesAndScripts(
            os.path.join(plugin_location, "j2", "js"),
            os.path.join(output_dir, "js"),
        )
        copyfile(
            os.path.join(
                self.infrastructure.settings.module_path, "images", "favicon.png"
            ),
            os.path.join(output_dir, "images", "favicon.png"),
        )

        html_template_file = "pair_report_index_page.html"

        html_index_filename = os.path.join(output_dir, "index.html")

        template_keywords = self.infrastructure.getCommonJinjaKeywords()

        self.infrastructure.jinja_configurator.configureTemplateWrite(
            html_template_file, html_index_filename, template_keywords
        )

        # Generate subpages
        for html_content in self.html_contents:
            html_content.exportFiles(self.infrastructure.jinja_configurator)

        self.log(f"Multi page html pair report written to directory '{output_dir}'")
