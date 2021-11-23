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
from elf_diff.plugin import (
    ExportPairReportPlugin,
    PluginConfigurationKey,
    PluginConfigurationInformation,
)
from elf_diff.jinja import Configurator
from elf_diff.symbol import Symbol
from elf_diff.auxiliary import recursiveCopy, getDirectoryThatStoresModule
from elf_diff.instruction_collector import SOURCE_CODE_START_TAG, SOURCE_CODE_END_TAG
from elf_diff.pair_report_document import ValueTreeNode
from elf_diff.settings import Settings
import os
from shutil import copyfile
import difflib
import sys
from typing import Callable, Optional, Dict, List, Type

DEFAULT_SINGLE_PAGE_REPORT_OUTPUT_FILE = "elf_diff_report.html"
DEFAULT_MULTI_PAGE_REPORT_DIR = "elf_diff_report"
DEFAULT_TEMPLATE_DIRECTORY: str = os.path.join(
    getDirectoryThatStoresModule(sys.modules[__name__]), "j2"
)


def postHighlightSourceCode(src: str) -> str:
    """Replace start and end tags in tagged source code with HTML spans
    in order to allow for CSS based formatting"""
    return src.replace(SOURCE_CODE_START_TAG, '<span class="source">').replace(
        SOURCE_CODE_END_TAG, "</span>"
    )


def getDifferencesAsHTML(old_symbol: ValueTreeNode, new_symbol: ValueTreeNode) -> str:
    """Generate a tabular formatted version of the differences of the
    assembly instructions of two symbols
    """
    if old_symbol.type == Symbol.TYPE_DATA:
        return "Data symbol -> no assembly"
    elif old_symbol.instructions == new_symbol.instructions:
        return "Instructions unchanged"

    old_instruction_lines: str = old_symbol.instructions.split("\n")
    new_instruction_lines: str = new_symbol.instructions.split("\n")

    diff_class = difflib.HtmlDiff(tabsize=3, wrapcolumn=200)

    diff_table: str = diff_class.make_table(
        old_instruction_lines,
        new_instruction_lines,
        fromdesc="Old",
        todesc="New",
        context=True,
        numlines=1000,
    )

    return postHighlightSourceCode(diff_table)


class PluginScope(object):
    """Stores relevant information used across the scope of the plugin"""

    def __init__(self) -> None:
        self.skip_symbol_similarities: bool
        self.consider_equal_sized_identical: bool
        self.single_page: bool
        self.jinja_configurator: Configurator
        self.output_dir: str
        self.document: ValueTreeNode

    def getCommonJinjaKeywords(self) -> dict:
        """Get Jinja keywords that are used in all template files"""
        return {"is_single_page_report": self.single_page, "document": self.document}


class Content(object):
    """An abstract representation of (HTML) content.
    The content can either be exported to individual files or
    provided as a string in order to be stored in
    another HTML file by configuring a Jinja template.
    """

    def __init__(self) -> None:
        """Initializes content of a frame or a file"""
        self._template_keywords: dict
        self._html: str
        self._plugin_scope: PluginScope

    def prepareTemplateKeywords(self) -> None:
        """Prepare Jinja2 keywords used for template configuration"""
        pass

    def generateHTML(self) -> None:
        """Generate html content to be output in Jinja2 templates
        content is expected to be stored in self._html
        """
        pass

    def getOutputFilepath(self) -> str:  # pylint: disable=no-self-use
        """Return the output filename assocrated with the HTML content"""
        pass

    def getRelPathToIndexFileDirectory(self) -> str:
        """Return the relative path from the location of the html file
        that stores the HTML file and the directory that holds
        the index.html file
        """
        pass

    def getTitle(self) -> str:  # pylint: disable=no-self-use
        """Return a title that relates to the content"""
        return ""

    def getHTML(self) -> str:
        """Return the generated HTML content"""
        self.prepareTemplateKeywords()
        self.generateHTML()
        return self._html

    def exportFiles(self) -> None:
        """Export files associated with the content"""
        self.prepareTemplateKeywords()
        self.generateHTML()

        template_file = "frame_content.html"

        html_output_file: str = os.path.join(
            self._plugin_scope.output_dir, self.getOutputFilepath()
        )

        template_keywords: dict = self._plugin_scope.getCommonJinjaKeywords()

        template_keywords.update(
            {
                "page_title": self.getTitle(),
                "content_html": self._html,
                "index_file_directory": self.getRelPathToIndexFileDirectory(),
            }
        )

        self._plugin_scope.jinja_configurator.configureTemplateWrite(
            template_file=template_file,
            output_file=html_output_file,
            template_keywords=template_keywords,
        )


class SymbolClassProperties(object):
    """Common properties of a symbol class
    (appeared, disappeared, persisting, similar)
    """

    def __init__(
        self,
        class_: str,
        id_getter: Callable,
        name_getter: Callable,
        additional_overview_content: Optional[str] = None,
        symbol_class_alias_getter: Optional[Callable] = None,
        update_entity_keywords: Optional[Callable] = None,
    ):
        self.class_: str = class_
        self.id_getter: Callable = id_getter
        self.name_getter: Callable = name_getter
        self.additional_overview_content: Optional[str] = additional_overview_content
        self.symbol_class_alias_getter: Callable = symbol_class_alias_getter or (
            lambda symbol_class_properties: symbol_class_properties.class_
        )
        self.update_entity_keywords: Callable = update_entity_keywords or (
            lambda symbol, keywords: None
        )


class SymbolEntity(Content):
    """Represents the content associated with a symbol of one of the symbol classes
    (appeared, disappeared, persisting, similar)
    """

    def __init__(
        self,
        symbol_of_class: ValueTreeNode,
        symbol_class_properties: SymbolClassProperties,
        plugin_scope: PluginScope,
    ):
        """Initialize the symbol entity"""
        super().__init__()
        self._symbol_of_class: ValueTreeNode = symbol_of_class
        self._symbol_class_properties: SymbolClassProperties = symbol_class_properties
        self._plugin_scope: PluginScope = plugin_scope

    def prepareTemplateKeywords(self) -> None:
        """Prepares the keywords used for configuring a related Jinja template file"""
        if hasattr(self, "_template_keywords"):
            return

        self._template_keywords = self._plugin_scope.getCommonJinjaKeywords()
        self._template_keywords.update(
            {
                "symbol": self._symbol_of_class,
                "symbol_class": self._symbol_class_properties.class_,
            }
        )
        self._symbol_class_properties.update_entity_keywords(
            self._symbol_of_class, self._template_keywords
        )

    def getOutputFilepath(self) -> str:
        """Get the filepath of the output file associated with the symbol entity.
        The path is meant to be a subpath below the directory that stores
        index.html
        """
        symbol_id: int = self._symbol_class_properties.id_getter(
            self._symbol_of_class
        )  # type(self) is necessary as there is some strange behavior class variable lambdas
        return os.path.join(
            "details", self._symbol_class_properties.class_, "%s.html" % symbol_id
        )

    def getTitle(self) -> str:
        """Return the title of the symbol entity (page/section)"""
        symbol_name: str = self._symbol_class_properties.name_getter(
            self._symbol_of_class
        )  # type(self) is necessary as there is some strange behavior class variable lambdas
        return "%s Symbol %s" % (
            self._symbol_class_properties.class_.capitalize(),
            symbol_name,
        )

    def generateHTML(self) -> None:
        """Generate the HTML code associated with the symbol entity"""

        if hasattr(self, "_html"):
            return

        self.prepareTemplateKeywords()

        # Appeared and disappeared symbols use the same Jinja template files.
        # We use "isolated" as name for the joint symbol class in filenames.
        symbol_class_alias: str = (
            self._symbol_class_properties.symbol_class_alias_getter(
                self._symbol_class_properties
            )
        )
        html_template_file: str = f"{symbol_class_alias}_symbol_details.html"

        self._html: str = self._plugin_scope.jinja_configurator.configureTemplate(
            template_file=html_template_file, template_keywords=self._template_keywords
        )

    def getRelPathToIndexFileDirectory(self):
        """Return the relative path from the file whose content is represented
        by this class to the directory that holds the index.html
        """
        if self._plugin_scope.single_page is False:
            return os.path.join("..", "..")
        return "."


class SymbolOverview(Content):
    """Content of symbol overview tables"""

    def __init__(
        self, symbol_class_properties: SymbolClassProperties, plugin_scope: PluginScope
    ):
        """Initialize the similar symbols overview class."""
        super().__init__()
        self._symbol_class_properties: SymbolClassProperties = symbol_class_properties
        self._plugin_scope: PluginScope = plugin_scope

    def generateHTML(self) -> None:
        """Generate the HTML code of the symbol overview table"""

        if hasattr(self, "_html"):
            return

        symbol_class: str = self._symbol_class_properties.class_

        symbols_of_class: dict = getattr(
            self._plugin_scope.document.symbols, symbol_class
        )
        if len(symbols_of_class) == 0:
            self._html = f"No {symbol_class} symbols"
            return

        template_keywords: dict = self._plugin_scope.getCommonJinjaKeywords()
        template_keywords.update(
            {"symbols": symbols_of_class.values(), "symbol_class": symbol_class}
        )

        if self._symbol_class_properties.symbol_class_alias_getter is None:
            raise Exception("Missing symbol_class_alias_getter")
        symbol_class_alias: str = (
            self._symbol_class_properties.symbol_class_alias_getter(
                self._symbol_class_properties
            )
        )
        html_template_file: str = f"{symbol_class_alias}_symbol_overview.html"

        self._html: str = self._plugin_scope.jinja_configurator.configureTemplate(
            template_file=html_template_file, template_keywords=template_keywords
        )

        if self._symbol_class_properties.additional_overview_content is not None:
            self._html += self._symbol_class_properties.additional_overview_content

    def getOutputFilepath(self) -> str:  # pylint: disable=no-self-use
        """Return the relative path of the output file from the directory that holds the
        index.html
        """
        return f"{self._symbol_class_properties.class_}_symbols_overview.html"

    def getTitle(self) -> str:  # pylint: disable=no-self-use
        """Return the title associated with the HTML content"""
        return "%s Symbols Overview" % self._symbol_class_properties.class_.capitalize()

    def getRelPathToIndexFileDirectory(self) -> str:
        """Return the relative path from the directory that holds the file
        associated with the overview html content to the directory that holds
        index.html
        """
        return "."


class SymbolDetails(Content):
    """HTML content assoicated with symbol details"""

    def __init__(
        self, symbol_class_properties: SymbolClassProperties, plugin_scope: PluginScope
    ):
        """Initialize the symbols details class."""
        super().__init__()
        self._symbol_class_properties: SymbolClassProperties = symbol_class_properties
        self._plugin_scope: PluginScope = plugin_scope

    def generateHTML(self) -> None:
        """Generate the HTML that represents the symbol details"""
        if hasattr(self, "_html"):
            return

        symbols_of_class: dict = getattr(
            self._plugin_scope.document.symbols, self._symbol_class_properties.class_
        )

        symbols_listed = False
        html_lines = []

        for symbol_of_class in symbols_of_class.values():

            symbols_listed = True

            if symbol_of_class.display_info.display_symbol_details is False:
                continue

            symbol_entity = SymbolEntity(
                symbol_of_class=symbol_of_class,
                symbol_class_properties=self._symbol_class_properties,
                plugin_scope=self._plugin_scope,
            )
            symbol_entity.generateHTML()

            html_lines.append(symbol_entity.getHTML())

        if not symbols_listed:
            self._html = f"No {self._symbol_class_properties.class_} functions or no symbol changes"
            return

        self._html = "\n".join(html_lines)

    def exportFiles(self) -> None:
        """Export HTML files that hold the symbol details information"""
        if self._plugin_scope.single_page is True:
            return

        symbol_class: str = self._symbol_class_properties.class_
        symbols_of_class: dict = getattr(
            self._plugin_scope.document.symbols, symbol_class
        )

        for symbol_of_class in symbols_of_class.values():
            if symbol_of_class.display_info.display_symbol_details is False:
                continue
            symbol_entity = SymbolEntity(
                symbol_of_class=symbol_of_class,
                symbol_class_properties=self._symbol_class_properties,
                plugin_scope=self._plugin_scope,
            )

            symbol_entity.generateHTML()
            symbol_entity.exportFiles()


class StatisticsOverview(Content):
    """HTML content of overall statistics of symbols"""

    def __init__(self, plugin_scope: PluginScope):
        """Initialize the statistics overview class."""
        super().__init__()
        self._plugin_scope: PluginScope = plugin_scope

    def prepareTemplateKeywords(self) -> None:
        """Prepare Jinja template keywords that configure the statistics overview
        template file.
        """
        if hasattr(self, "_template_keywords"):
            return

        self._template_keywords: Dict[
            str, Type
        ] = self._plugin_scope.getCommonJinjaKeywords()

    def generateHTML(self) -> None:
        """Generate the HTML representation of the statistics content"""

        if hasattr(self, "_html"):
            return

        html_template_file = "statistics.html"

        self._html = self._plugin_scope.jinja_configurator.configureTemplate(
            html_template_file, self._template_keywords
        )

    def getOutputFilepath(self) -> str:  # pylint: disable=no-self-use
        """Return the relative path from the directory that holds index.html
        to the statistics file
        """
        return "statistics.html"

    def getTitle(self) -> str:  # pylint: disable=no-self-use
        """Return the title of the statistics page/frame/section"""
        return "Statistics"

    def getRelPathToIndexFileDirectory(self) -> str:
        """Get the relative path from the directory that holds the statistics file
        to the directory that holds index.html
        """
        return "."


class DocumentPage(Content):
    """Content of a HTML page that displays the document tree"""

    def __init__(self, plugin_scope: PluginScope):
        """Initialize the document page class."""
        super().__init__()
        self._plugin_scope: PluginScope = plugin_scope

    def prepareTemplateKeywords(self) -> None:
        """Prepare the template keywords the configure the document page's
        Jinja template file
        """
        if hasattr(self, "_template_keywords"):
            return

        self._template_keywords: dict = self._plugin_scope.getCommonJinjaKeywords()

    def generateHTML(self) -> None:
        """Generate the HTML code of the documents page"""
        if hasattr(self, "_html"):
            return

        html_template_file = "document.html"

        self._html: str = self._plugin_scope.jinja_configurator.configureTemplate(
            html_template_file, self._template_keywords
        )

    def getOutputFilepath(self) -> str:  # pylint: disable=no-self-use
        """Get the path from the directory that holds index.html to the
        HTML output file
        """
        return "document.html"

    def getTitle(self) -> str:  # pylint: disable=no-self-use
        """Get the title of the document page"""
        return "Document"

    def getRelPathToIndexFileDirectory(self) -> str:
        """Get the relative path from the directory that holds the document
        file to the directory that holds index.html
        """
        return "."


class HTMLExportPairReportPlugin(ExportPairReportPlugin):
    """A plugin class that exports the elf_diff document as either
    a single HTML page or a set of HMTL pages in a subdirectory
    """

    SYMBOL_CLASSES = ["persisting", "appeared", "disappeared", "similar", "migrated"]
    INFORMATION_TYPES = ["overview", "detail"]

    def __init__(self, settings: Settings, plugin_configuration: Dict[str, str]):
        """Initialize the pair report class."""
        super().__init__(settings, plugin_configuration)

        jinja_template_dir: str = self.getConfigurationParameter(name="template_dir")

        plugin_scope = PluginScope()
        plugin_scope.skip_symbol_similarities = bool(
            self._settings.skip_symbol_similarities
        )
        plugin_scope.consider_equal_sized_identical = bool(
            self._settings.consider_equal_sized_identical
        )
        if self.getConfigurationParameter("single_page") == "True":
            plugin_scope.single_page = True
        else:
            plugin_scope.single_page = False
        plugin_scope.jinja_configurator = Configurator(
            self._settings, jinja_template_dir
        )
        if self.isConfigurationParameterAvailable("output_dir"):
            plugin_scope.output_dir = self.getConfigurationParameter("output_dir")

        self._plugin_scope = plugin_scope

        self.symbol_overviews: Dict[str, SymbolOverview] = {}
        self.symbol_details: Dict[str, SymbolDetails] = {}

        self.statistics_overview: StatisticsOverview
        self.document_page: DocumentPage

        self._html_contents: List[Content] = []

        self._content_is_prepared = False

    def export(self, document: ValueTreeNode) -> None:
        """Export files (plugin interface method)"""
        self._plugin_scope.document = document

        if self._plugin_scope.single_page:
            self.exportSinglePage()
        else:
            self.exportMultiPage()

    def registerContent(self, html_content: Content) -> None:
        """Register a Content object"""
        self._html_contents.append(html_content)

    def prepareContentForSymbolsOfClass(
        self, symbol_class_properties: SymbolClassProperties
    ) -> None:
        """Prepare symbols of a specific class defined by the symbol class properties"""
        symbol_overview = SymbolOverview(
            symbol_class_properties=symbol_class_properties,
            plugin_scope=self._plugin_scope,
        )
        self.registerContent(symbol_overview)
        self.symbol_overviews[symbol_class_properties.class_] = symbol_overview

        symbol_details = SymbolDetails(
            symbol_class_properties, plugin_scope=self._plugin_scope
        )
        self.registerContent(symbol_details)
        self.symbol_details[symbol_class_properties.class_] = symbol_details

    def preparePersistingSymbolsContent(self) -> None:
        """Prepare persisting symbols"""
        additional_overview_content = None
        if self._plugin_scope.consider_equal_sized_identical:
            additional_overview_content = "Equal sized symbols forcefully ignored."

        symbol_class_properties = SymbolClassProperties(
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
        self.prepareContentForSymbolsOfClass(symbol_class_properties)

    def prepareMigratedSymbolsContent(self) -> None:
        """Prepare migrated symbols"""

        symbol_class_properties = SymbolClassProperties(
            class_="migrated",
            id_getter=lambda symbol: symbol.related_symbols.old.id,
            name_getter=lambda symbol: symbol.related_symbols.old.name,
        )
        self.prepareContentForSymbolsOfClass(symbol_class_properties)

    def prepareIsolatedSymbolsContent(self, symbol_class: str) -> None:
        """Prepare isolated symbols of a symbol class (appeared/disappeared)"""
        symbol_class_properties = SymbolClassProperties(
            class_=symbol_class,
            id_getter=lambda symbol: symbol.actual.id,
            name_getter=lambda symbol: symbol.actual.name,
            symbol_class_alias_getter=lambda _: "isolated",
        )
        self.prepareContentForSymbolsOfClass(symbol_class_properties)

    def prepareAppearedSymbolsContent(self) -> None:
        """Prepare appeared symbols"""
        self.prepareIsolatedSymbolsContent(symbol_class="appeared")

    def prepareDisappearedSymbolsContent(self) -> None:
        """Prepare disappeared symbols"""
        self.prepareIsolatedSymbolsContent(symbol_class="disappeared")

    def prepareSimilarSymbolsContent(self) -> None:
        """Prepare similar symbols"""
        symbol_class_properties = SymbolClassProperties(
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
        self.prepareContentForSymbolsOfClass(symbol_class_properties)

    def prepareStatisticsContent(self) -> None:
        """Prepare the statistics page content"""
        self.statistics_overview = StatisticsOverview(self._plugin_scope)
        self.registerContent(self.statistics_overview)

    def prepareDocumentPageContent(self) -> None:
        """Prepare the content of the document page"""
        self.document_page = DocumentPage(self._plugin_scope)
        self.registerContent(self.document_page)

    def prepareContent(self) -> None:
        """Prepare all HTML content"""
        if self._content_is_prepared:
            return

        self.prepareStatisticsContent()
        self.prepareDocumentPageContent()

        self.preparePersistingSymbolsContent()
        self.prepareDisappearedSymbolsContent()
        self.prepareAppearedSymbolsContent()

        if not self._plugin_scope.skip_symbol_similarities:
            self.prepareSimilarSymbolsContent()

        self.prepareMigratedSymbolsContent()

        self._content_is_prepared = True

    def exportSinglePage(self) -> None:
        """Export the document as a single HTML page"""

        output_file: str = self.getConfigurationParameter("output_file")

        self.prepareContent()

        template_file = "pair_report_single_page.html"

        template_keywords: dict = self._plugin_scope.getCommonJinjaKeywords()

        # Setup jinja keywords for overview/details of persisting, appeared, disappeared and similar symbols
        for information_type in self.INFORMATION_TYPES:
            contents = getattr(self, f"symbol_{information_type}s")
            for symbol_class in self.SYMBOL_CLASSES:
                # Some symbol classes like 'similar' may be suppressed by users choice
                if symbol_class in contents.keys():
                    content = contents[symbol_class]
                    content_html: str = ""
                    if content is not None:
                        content_html = content.getHTML()
                    template_keywords[
                        f"{symbol_class}_symbol_{information_type}"
                    ] = content_html

        template_keywords.update(
            {
                "statistics": self.statistics_overview.getHTML(),
                "skip_symbol_similarities": self._plugin_scope.skip_symbol_similarities,
            }
        )

        self._plugin_scope.jinja_configurator.configureTemplateWrite(
            template_file=template_file,
            output_file=output_file,
            template_keywords=template_keywords,
        )

        self.log(f"Single page html pair report written to directory '{output_file}'")

    def exportMultiPage(self) -> None:
        """Export the document as a multi page HTML document"""

        output_dir: str = self.getConfigurationParameter("output_dir")

        self.prepareContent()

        dirs: List[str] = [
            output_dir,
            os.path.join(output_dir, "details"),
            os.path.join(output_dir, "details", "persisting"),
            os.path.join(output_dir, "details", "disappeared"),
            os.path.join(output_dir, "details", "appeared"),
            os.path.join(output_dir, "details", "similar"),
            os.path.join(output_dir, "details", "migrated"),
            os.path.join(output_dir, "images"),
        ]

        for dir_ in dirs:
            if not os.path.exists(dir_):
                os.mkdir(dir_)

        plugin_module_path: str = self.getModulePath()

        recursiveCopy(
            os.path.join(plugin_module_path, "j2", "css"),
            os.path.join(output_dir, "css"),
        )
        recursiveCopy(
            os.path.join(plugin_module_path, "j2", "js"),
            os.path.join(output_dir, "js"),
        )
        copyfile(
            os.path.join(self._settings.module_path, "images", "favicon.png"),
            os.path.join(output_dir, "images", "favicon.png"),
        )

        html_template_file = "pair_report_index_page.html"

        html_index_file: str = os.path.join(output_dir, "index.html")

        template_keywords: dict = self._plugin_scope.getCommonJinjaKeywords()

        self._plugin_scope.jinja_configurator.configureTemplateWrite(
            template_file=html_template_file,
            output_file=html_index_file,
            template_keywords=template_keywords,
        )

        # Generate subpages
        for html_content in self._html_contents:
            html_content.exportFiles()

        self.log(f"Multi page html pair report written to directory '{output_dir}'")

    @staticmethod
    def getConfigurationInformation() -> PluginConfigurationInformation:
        """Return plugin configuration information"""
        return [
            PluginConfigurationKey(
                "single_page",
                "If True, a single-page HTML report will be exported, multi-page otherwise",
                is_optional=True,
                default="False",
            ),
            PluginConfigurationKey(
                "output_file",
                "The output file that is used for single-page report (default ",
                is_optional=True,
                default=DEFAULT_SINGLE_PAGE_REPORT_OUTPUT_FILE,
            ),
            PluginConfigurationKey(
                "output_dir",
                "The output directory that is used for multi-page report",
                is_optional=True,
                default=DEFAULT_MULTI_PAGE_REPORT_DIR,
            ),
            PluginConfigurationKey(
                "template_dir",
                "The directory where Jinja2 templates are read from",
                is_optional=True,
                default=DEFAULT_TEMPLATE_DIRECTORY,
            ),
        ] + super(
            HTMLExportPairReportPlugin, HTMLExportPairReportPlugin
        ).getConfigurationInformation()
