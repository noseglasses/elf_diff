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

# A jinja document is a tree structure of nested class objects that contains all information
# that is meant to be rendered or exported.
#
# To enable validation and documentation of the tree, two individual trees are maintained
# whose nodes are cross-linked on each level.
#
# The leaf nodes of the value tree represent the values that are typically used when rendering
# documents by e.g. specifying expressions as document.statistics.overall.new.resource_consumption.text = "some text"
#
# The nodes of the meta tree store information about what is stored, e.g. the data types
# their documentation and means of validating the corresponding value tree nodes.

import elf_diff.binary as binary
from elf_diff.binary import Binary
from elf_diff.binary_pair import BinaryPair, BinaryPairSettings
from elf_diff.git import gitRepoInfo
import elf_diff.string_diff as string_diff
from elf_diff.symbol import Symbol as ElfSymbol
from elf_diff.binary_pair import SimilarityPair
from elf_diff.settings import Settings
from elf_diff.meta_tree import Node, Value, Multiple
from elf_diff.value_tree import Node as ValueTreeNode
from elf_diff.meta_tree_properties import Properties, Doc, Type, AliasType
import datetime
import sys
import progressbar  # type: ignore # Make mypy ignore this module
from typing import Dict, Union, Tuple, Any, Optional, Collection

ELF_DIFF_DOCUMENT_VERSION = 1


def _typeName(obj: Any) -> str:
    """Returns the (shortest possible) type name of an object"""
    return type(obj).__name__


def _incIndent(indent: str) -> str:
    """Increase the indentation based on an already present indentation"""
    return f"{indent}   "


def _validateSettings(settings) -> None:
    """Validate relevant information of the injected settings object"""
    if not settings.old_binary_filename:
        raise Exception("No old binary filename defined")

    if not settings.new_binary_filename:
        raise Exception("No new binary filename defined")


def _configureChildValueTreeNode(
    name: str, value_tree_node: ValueTreeNode, **kwargs
) -> None:
    """Configure a given child value tree node"""
    child_value_tree_node: ValueTreeNode = value_tree_node.getChild(name)
    child_value_tree_node.getMetaTreeNode().configureValueTree(
        child_value_tree_node, **kwargs
    )


def _generateValueTree(
    node: Node, parent_value_tree_node: Optional[ValueTreeNode] = None
) -> ValueTreeNode:
    """Recursively attach a value tree to the meta tree"""
    value_tree_node = ValueTreeNode()
    value_tree_node.attachMetaTreeNode(node)

    for value in node._values.values():
        setattr(value_tree_node, value._name, None)

    if parent_value_tree_node is not None:
        parent_value_tree_node.addChild(node._name, value_tree_node)

    node.forEachChild(
        lambda parent, child, value_tree_node=value_tree_node: _generateValueTree(
            child, value_tree_node
        )
    )

    return value_tree_node


class Symbol(Node):
    """A general symbol"""

    def __init__(self):
        super().__init__(
            "symbol",
            Value("name", Doc("The symbol name (demangled if supported)"), Type(str)),
            Value("name_mangled", Doc("The mangled symbol name"), Type(str)),
            Value(
                "is_demangled", Doc("True if the symbol name is demangled"), Type(bool)
            ),
            Value(
                "type",
                Doc(
                    "Type character matching the characters used by the nm binutils tool"
                ),
                Type(str),
            ),
            Value("id", Doc("Unique symbol identifier"), Type(int)),
            Value("size", Doc("Number of bytes occupied by the symbol"), Type(int)),
            Value(
                "instructions",
                Doc(
                    "Code instructions (assembly with possibly high level language code intermixed)"
                ),
                Type(str),
            ),
            Value(
                "is_stored_in_program_memory",
                Doc("True if the symbol is stored in program memory"),
                Type(bool),
            ),
            Node(
                "source",
                Doc("Information about the symbols source definition"),
                Value("file_id", Doc("The id of the source file"), Type(int)),
                Value(
                    "line",
                    Doc(
                        "The line number in the source file where the symbol is defined"
                    ),
                    Type(int),
                ),
                # Value(
                #    "column",
                #    Doc(
                #        "The column number in the source file where the symbol is defined"
                #    ),
                #    Type(int),
                # ),
            ),
        )
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the symbol meta tree node's value tree representation from an ElfSymbol"""
        symbol: ElfSymbol = kwargs["symbol"]
        value_tree_node.name = symbol.name
        value_tree_node.name_mangled = symbol.name_mangled
        value_tree_node.is_demangled = symbol.is_demangled
        value_tree_node.type = symbol.type_
        value_tree_node.id = symbol.id_
        value_tree_node.size = symbol.size
        value_tree_node.instructions = symbol.instructions
        value_tree_node.is_stored_in_program_memory = symbol.livesInProgramMemory()
        value_tree_node.source.file_id = symbol.source_id
        value_tree_node.source.line = symbol.source_line
        # value_tree_node.source.column = symbol.source_column


class DisplayInfo(Node):
    """An auxiliary display info node shared by other custom nodes"""

    def __init__(self):
        super().__init__(
            "display_info",
            Properties(Doc("Information that configures how things are displayed")),
            Value(
                "symbol_class",
                Doc(
                    "The class of symbol old/new/appeared/disappeared/persisting/similar"
                ),
                Type(str),
            ),
            Value(
                "anchor_id",
                Doc(
                    "Unique string identifier token that can be used to generate a HTML anchor for cross references"
                ),
                Type(str),
            ),
            Value(
                "display_symbol_details",
                Doc("True if symbol details are supposed to be displayed"),
                Type(bool),
            ),
        )

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the display info object's associated value tree node from one or two symbols"""
        symbol_class: str = kwargs["symbol_class"]
        symbol1: ElfSymbol = kwargs["symbol1"]
        symbol2: ElfSymbol = kwargs.get("symbol2", symbol1)
        if symbol2 is None:
            symbol2 = symbol1

        if (
            (symbol1.type_ == ElfSymbol.TYPE_DATA)
            or (not symbol1.hasInstructions())
            or (not symbol2.hasInstructions())
        ):
            display_symbol_details = False
        else:
            display_symbol_details = True

        value_tree_node.symbol_class = symbol_class
        value_tree_node.anchor_id = str(symbol1.id_)
        value_tree_node.display_symbol_details = display_symbol_details


class RelatedSymbols(Node):
    """Represents related symbols of a persisting symbol or a similar symbols pair"""

    def __init__(self):
        super().__init__(
            "related_symbols",
            Properties(Doc("A relation between two symbols")),
            Value(
                "size_delta",
                Doc(
                    "Difference in bytes between the resource occupation of the two symbols"
                ),
                Type(int),
            ),
            Value("old", Doc("The old symbol"), Type(ValueTreeNode), AliasType(Symbol)),
            Value("new", Doc("The new symbol"), Type(ValueTreeNode), AliasType(Symbol)),
        )

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configures the related symbol node's associated value tree node"""
        old_symbol: ElfSymbol = kwargs["old_symbol"]
        new_symbol: ElfSymbol = kwargs["new_symbol"]
        value_tree_node.size_delta = new_symbol.size - old_symbol.size


class IsolatedSymbol(Node):
    """An isolated symbol (either appeared or disappeared)"""

    def __init__(self, symbol_class: str):
        self._symbol_class = symbol_class
        super().__init__(
            f"{symbol_class}_symbol",
            DisplayInfo(),
            Value(
                "actual",
                Doc("The actual symbol"),
                Type(ValueTreeNode),
                AliasType(Symbol),  # , DynamicValue(lambda value: value.id))
            ),
        )
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the isolated symbol's associated value tree node"""
        settings: Settings = kwargs["settings"]
        symbol: ElfSymbol = kwargs["symbol"]
        _configureChildValueTreeNode(
            "display_info",
            value_tree_node,
            settings=settings,
            symbol_class=self._symbol_class,
            symbol1=symbol,
        )


class AppearedSymbol(IsolatedSymbol):
    """An appeared symbol"""

    def __init__(self):
        super().__init__(symbol_class="appeared")


class DisappearedSymbol(IsolatedSymbol):
    """An disappeared symbol"""

    def __init__(self):
        super().__init__(symbol_class="disappeared")


class PersistingSymbol(Node):
    """A persisting symbol"""

    def __init__(self):
        super().__init__("persisting_symbol", DisplayInfo(), RelatedSymbols())
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the persisting symbol's associated value tree node indirectly
        by configuring the meta tree nodes"""
        settings: Settings = kwargs["settings"]
        old_symbol: Symbol = kwargs["old_symbol"]
        new_symbol: Symbol = kwargs["new_symbol"]
        _configureChildValueTreeNode(
            "display_info",
            value_tree_node,
            settings=settings,
            symbol_class="persisting",
            symbol1=old_symbol,
            symbol2=new_symbol,
        )
        _configureChildValueTreeNode(
            "related_symbols",
            value_tree_node,
            old_symbol=old_symbol,
            new_symbol=new_symbol,
        )


class MigratedSymbol(Node):
    """A migrated symbol"""

    def __init__(self):
        super().__init__("migrated_symbol", DisplayInfo(), RelatedSymbols())
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the migrated symbol's associated value tree node indirectly
        by configuring the meta tree nodes"""
        settings: Settings = kwargs["settings"]
        old_symbol: Symbol = kwargs["old_symbol"]
        new_symbol: Symbol = kwargs["new_symbol"]
        _configureChildValueTreeNode(
            "display_info",
            value_tree_node,
            settings=settings,
            symbol_class="migrated",
            symbol1=old_symbol,
            symbol2=new_symbol,
        )
        _configureChildValueTreeNode(
            "related_symbols",
            value_tree_node,
            old_symbol=old_symbol,
            new_symbol=new_symbol,
        )


class SimilarSymbols(Node):
    """A similar symbols pair"""

    def __init__(self):
        super().__init__(
            "similar_symbols",
            DisplayInfo(),
            RelatedSymbols(),
            Value("id", Doc("The id of the symbol pair"), Type(int)),
            Multiple(
                ("old", "new"),
                Node(
                    None,
                    Value(
                        "signature_tagged",
                        Doc(
                            "A tagged version of the symbol signature. Taggs '%s' and '%s' must be replaced accordingly, e.g. for highlighting."
                            % (
                                string_diff.HIGHLIGHT_START_TAG,
                                string_diff.HIGHLIGHT_END_TAG,
                            )
                        ),
                        Type(str),
                    ),
                ),
            ),
            Node(
                "similarities",
                Properties(Doc("Symbol similarity ratios"), Type(float)),
                Value(
                    "signature", Doc("The percentage of symbol signature similarity")
                ),
                Value(
                    "instruction",
                    Doc("The percentage of symbol instruction similarity"),
                ),
            ),
        )
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the meta tree node's value tree representation from a pair of similar symbols"""
        settings: Settings = kwargs["settings"]
        similarity_pair: SimilarityPair = kwargs["similarity_pair"]
        id_: int = kwargs["id_"]
        instruction_similarity = 1.0
        if similarity_pair.instruction_similarity is not None:
            instruction_similarity = similarity_pair.instruction_similarity * 100.0

        _configureChildValueTreeNode(
            "display_info",
            value_tree_node,
            settings=settings,
            symbol_class="similar",
            symbol1=similarity_pair.old_symbol,
            symbol2=similarity_pair.new_symbol,
        )
        _configureChildValueTreeNode(
            "related_symbols",
            value_tree_node,
            old_symbol=similarity_pair.old_symbol,
            new_symbol=similarity_pair.new_symbol,
        )

        value_tree_node.id = id_
        value_tree_node.old.signature_tagged = string_diff.tagStringDiffSource(
            similarity_pair.old_symbol.name,
            similarity_pair.new_symbol.name,
        )
        value_tree_node.new.signature_tagged = string_diff.tagStringDiffTarget(
            similarity_pair.old_symbol.name,
            similarity_pair.new_symbol.name,
        )
        value_tree_node.similarities.signature = (
            similarity_pair.signature_similarity * 100.0
        )
        value_tree_node.similarities.instruction = instruction_similarity


class SourceFile(Node):
    def __init__(self):
        super().__init__(
            "source_file",
            Value(
                "path",
                Doc("The full path of the source file as reported by binutils/nm"),
                Type(str),
            ),
            Value(
                "path_wo_prefix",
                Doc("The name of the source file with user defined prefix stripped"),
                Type(str),
            ),
            Value("id", Doc("The id of the source file"), Type(int)),
        )
        self.connectNodes()

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the source file"""
        source_file: binary.SourceFile = kwargs["source_file"]

        value_tree_node.path = source_file.path
        value_tree_node.path_wo_prefix = source_file.path_wo_prefix
        value_tree_node.id = source_file.id_


SYMBOL_TYPES: Tuple = (
    Symbol,
    PersistingSymbol,
    AppearedSymbol,
    DisappearedSymbol,
    SimilarSymbols,
    MigratedSymbol,
)

SymbolType = Union[
    Symbol,
    PersistingSymbol,
    AppearedSymbol,
    DisappearedSymbol,
    SimilarSymbols,
    MigratedSymbol,
]


class MetaDocument(Node):
    """A meta document"""

    def __init__(self):
        super().__init__(
            "document",
            Properties(Doc(None)),
            Node(
                "general",
                Properties(Doc("General information about the document")),
                Value(
                    "document_version",
                    Doc("The document version of this document"),
                    Type(int),
                ),
                Value("page_title", Doc("The title of the document page"), Type(str)),
                Value("doc_title", Doc("Document title"), Type(str)),
                Value(
                    "elf_diff_repo_root",
                    Doc("Path to the root of the elf_diff git repo"),
                    Type(str),
                ),
                Value(
                    "generation_date", Doc("The document generation date"), Type(str)
                ),
                Value(
                    "elf_diff_version",
                    Doc("The elf_diff version that generated the page"),
                    Type(str),
                ),
            ),
            Node(
                "configuration",
                Properties(
                    Doc(
                        "Boolean flags that configure what is supposed to be displayed and how"
                    ),
                    Type(bool),
                ),
                Value(
                    "instructions_available",
                    Doc("True if instructions could be read from both binary files"),
                ),
                Value(
                    "display_old_binary_info",
                    Doc("True if old binary info is supposed to be displayed"),
                ),
                Value(
                    "display_new_binary_info",
                    Doc("True if new binary info is supposed to be displayed"),
                ),
                Value(
                    "display_details",
                    Doc(
                        "True if symbol detail information is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_binary_details",
                    Doc("True if details about binaries are supposed to be displayed"),
                ),
                Value(
                    "display_build_info",
                    Doc("True if build information is supposed to be displayed"),
                ),
                Value(
                    "display_persisting_symbols_overview",
                    Doc(
                        "True if an overview about persisting symbols is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_disappeared_symbols_overview",
                    Doc(
                        "True if an overview about disappeared symbols is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_appeared_symbols_overview",
                    Doc(
                        "True if an overview about appeared symbols is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_similar_symbols_overview",
                    Doc(
                        "True if an overview about similar symbols is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_similar_symbols",
                    Doc("True if similar symbols are supposed to be displayed"),
                ),
                Value(
                    "display_migrated_symbols_overview",
                    Doc(
                        "True if an overview about migrated symbols is supposed to be displayed"
                    ),
                ),
                Value(
                    "display_migrated_symbols",
                    Doc("True if migrated symbols are supposed to be displayed"),
                ),
                Value(
                    "debug_info_available",
                    Doc(
                        "True if Dwarf debugging information was found in both binaries"
                    ),
                ),
            ),
            Value("old_binary_info", Doc("Info about the old binary"), Type(str)),
            Value("new_binary_info", Doc("Info about the new binary"), Type(str)),
            Value("build_info", Doc("Information about the build"), Type(str)),
            Node(
                "files",
                Properties(Doc("Information about relevant files")),
                Node(
                    "input",
                    Properties(Doc("Information about relevant input files")),
                    Multiple(
                        ("old", "new"),
                        Node(
                            None,
                            Value(
                                "binary_path",
                                Doc("The path to the binary file"),
                                Type(str),
                            ),
                            Value(
                                "debug_info_available",
                                Doc(
                                    "True if Dwarf debug info avaiable in the elf binary"
                                ),
                                Type(bool),
                            ),
                            Value(
                                "source_files",
                                Doc(
                                    "Source file by file id (dict values of type SourceFile)"
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            Node(
                "statistics",
                Node(
                    "overall",
                    Properties(Doc("Overall statistics")),
                    Multiple(
                        ("old", "new", "delta"),
                        Node(
                            None,
                            Properties(Doc(None)),
                            Node(
                                "resource_consumption",
                                Properties(
                                    Doc("Information about resource consumption"),
                                    Type(int),
                                ),
                                Value("code", Doc("Memory required to store code")),
                                Value("static_ram", Doc("Static RAM consumption")),
                                Value("text", Doc("text section memory consumption")),
                                Value("data", Doc("data section memory consumption")),
                                Value("bss", Doc("bss section memory consumption")),
                            ),
                        ),
                    ),
                ),
                Node(
                    "symbols",
                    Properties(Doc("Statistics of symbols")),
                    Multiple(
                        ("old", "new"),
                        Node(
                            None,
                            Properties(
                                Doc("Overall statistics about symbols considered")
                            ),
                            Node(
                                "count",
                                Properties(Doc("Number of symbols"), Type(int)),
                                Value("selected", Doc("Number of symbols selected")),
                                Value("dropped", Doc("Number of symbols dropped")),
                                Value(
                                    "total", Doc("Number of total symbols in binary")
                                ),
                            ),
                            Node(
                                "regex",
                                Properties(Type(str)),
                                Value(
                                    "selection",
                                    Doc(
                                        "Regular expression used to select symbols found in binary"
                                    ),
                                ),
                                Value(
                                    "exclusion",
                                    Doc(
                                        "Regular expression used to exclude symbols found in binary"
                                    ),
                                ),
                            ),
                        ),
                    ),
                    Multiple(
                        ("appeared", "disappeared"),
                        Node(
                            None,
                            Properties(Type(int), Doc(None)),
                            Value("count", Doc("Number of symbols")),
                        ),
                    ),
                    Node(
                        "persisting",
                        Properties(Doc(None)),
                        Value("count", Doc("Number of symbols"), Type(int)),
                        Node(
                            "resource_consumption",
                            Properties(
                                Doc(
                                    "Total resource consumption of considered symbols of given class"
                                ),
                                Type(int),
                            ),
                            Value(
                                "old",
                                Doc(
                                    "Overall number of bytes consumed in the old version"
                                ),
                            ),
                            Value(
                                "new",
                                Doc(
                                    "Overall number of bytes consumed in the old version"
                                ),
                            ),
                            Value(
                                "delta",
                                Doc(
                                    "Change to number of bytes consumed (only for persisting and similar)"
                                ),
                            ),
                        ),
                    ),
                    Node(
                        "similar",
                        Properties(Doc(None)),
                        Value("count", Doc("Number of symbols"), Type(int)),
                    ),
                ),
            ),
            Node(
                "symbols",
                Properties(Doc("Symbols by id/table id ")),
                Type(dict),
                Value(
                    "old",
                    Doc(
                        "Dict of selected symbols of the old binary by symbol id (dict values of type Symbol)"
                    ),
                ),
                Value(
                    "new",
                    Doc(
                        "Dict of selected symbols of the new binary by symbol id (dict values of type Symbol)"
                    ),
                ),
                Value(
                    "appeared",
                    Doc(
                        "Dict of appeared symbols by symbol id (dict values of type AppearedSymbol)"
                    ),
                ),
                Value(
                    "disappeared",
                    Doc(
                        "Disappeared symbols by symbol id (dict values of type DisappearedSymbol)"
                    ),
                ),
                Value(
                    "persisting",
                    Doc(
                        "Persisting symbols by symbol id (dict values of type PersistingSymbol)"
                    ),
                ),
                Value(
                    "similar",
                    Doc(
                        "Similar symbols by symbol id (dict values of type SimilarSymbols)"
                    ),
                ),
                Value(
                    "migrated",
                    Doc(
                        "Migrated symbols by symbol id (dict values of type MigratedSymbol)"
                    ),
                ),
            ),
        )
        self.connectNodes()

    @staticmethod
    def setupSymbolsDict(
        document: ValueTreeNode,
        settings: Settings,
        symbols: Collection[ElfSymbol],
        symbol_class: str,
    ) -> None:
        """Setup (new/old) elf symbols from a symbol list"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        node = Symbol()
        node._name = "%s_symbol" % symbol_class
        print(f"Adding {symbol_class} symbols to document")
        sys.stdout.flush()
        for symbol in progressbar.progressbar(symbols):
            value_tree = _generateValueTree(node)
            node.configureValueTree(value_tree, symbol=symbol)
            value_tree_nodes[symbol.id_] = value_tree

        setattr(document.symbols, symbol_class, value_tree_nodes)

    def setupOldSymbolsDict(self, document: ValueTreeNode, settings: Settings) -> None:
        """Setup a dictionary of old symbols"""
        MetaDocument.setupSymbolsDict(
            document, settings, self.binary_pair.old_binary.symbols.values(), "old"
        )

    def setupNewSymbolsDict(self, document: ValueTreeNode, settings: Settings) -> None:
        """Setup a dictionary of new symbols"""
        MetaDocument.setupSymbolsDict(
            document, settings, self.binary_pair.new_binary.symbols.values(), "new"
        )

    def setupPersistingSymbolsDict(
        self, document: ValueTreeNode, settings: Settings
    ) -> None:
        """Setup a dictionary of persisting symbols"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = PersistingSymbol()
        meta_node._name = "persisting_symbol"
        print("Adding persisting symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.persisting_symbol_names
        ):
            old_symbol: ElfSymbol = self.binary_pair.old_binary.symbols[symbol_name]
            new_symbol: ElfSymbol = self.binary_pair.new_binary.symbols[symbol_name]

            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(
                node, settings=settings, old_symbol=old_symbol, new_symbol=new_symbol
            )
            node.related_symbols.old = document.symbols.old[old_symbol.id_]
            node.related_symbols.new = document.symbols.new[new_symbol.id_]
            value_tree_nodes[old_symbol.id_] = node

        setattr(document.symbols, "persisting", value_tree_nodes)

    def setupAppearedSymbolsDict(
        self, document: ValueTreeNode, settings: Settings
    ) -> None:
        """Setup a dictionary of appeared symbols"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = AppearedSymbol()
        meta_node._name = "appeared_symbol"
        print("Adding appeared symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.appeared_symbol_names
        ):
            appeared_symbol: ElfSymbol = self.binary_pair.new_binary.symbols[
                symbol_name
            ]

            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(
                node, settings=settings, symbol=appeared_symbol
            )
            node.actual = document.symbols.new[appeared_symbol.id_]
            value_tree_nodes[appeared_symbol.id_] = node

        setattr(document.symbols, "appeared", value_tree_nodes)

    def setupDisappearedSymbolsDict(
        self, document: ValueTreeNode, settings: Settings
    ) -> None:
        """Setup a dictionary of disappeared symbols"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = DisappearedSymbol()
        meta_node._name = "disappeared_symbol"
        print("Adding disappeared symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.disappeared_symbol_names
        ):
            disappeared_symbol: ElfSymbol = self.binary_pair.old_binary.symbols[
                symbol_name
            ]

            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(
                node, settings=settings, symbol=disappeared_symbol
            )
            node.actual = document.symbols.old[disappeared_symbol.id_]
            value_tree_nodes[disappeared_symbol.id_] = node

        setattr(document.symbols, "disappeared", value_tree_nodes)

    def setupSimilarSymbolsDict(
        self, document: ValueTreeNode, settings: Settings
    ) -> None:
        """Setup a dictionary of similar symbol pairs"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = SimilarSymbols()
        meta_node._name = "similar_symbols"
        id_ = 0
        print("Adding similar symbols to document")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
            similarity_pair: SimilarityPair = self.binary_pair.similar_symbols[i]
            old_symbol = similarity_pair.old_symbol
            new_symbol = similarity_pair.new_symbol
            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(
                node, settings=settings, similarity_pair=similarity_pair, id_=id_
            )
            node.related_symbols.old = document.symbols.old[old_symbol.id_]
            node.related_symbols.new = document.symbols.new[new_symbol.id_]
            value_tree_nodes[id_] = node
            id_ += 1

        setattr(document.symbols, "similar", value_tree_nodes)

    def setupMigratedSymbolsDict(
        self, document: ValueTreeNode, settings: Settings
    ) -> None:
        """Setup a dictionary of migrated symbols"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = MigratedSymbol()
        meta_node._name = "migrated_symbol"
        print("Adding migrated symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.migrated_symbol_names
        ):
            old_symbol: ElfSymbol = self.binary_pair.old_binary.symbols[symbol_name]
            new_symbol: ElfSymbol = self.binary_pair.new_binary.symbols[symbol_name]

            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(
                node, settings=settings, old_symbol=old_symbol, new_symbol=new_symbol
            )
            node.related_symbols.old = document.symbols.old[old_symbol.id_]
            node.related_symbols.new = document.symbols.new[new_symbol.id_]
            value_tree_nodes[old_symbol.id_] = node

        setattr(document.symbols, "migrated", value_tree_nodes)

    @staticmethod
    def _setupSourceFilesDict(
        type_: str, source_files: Collection[binary.SourceFile]
    ) -> Dict[int, ValueTreeNode]:
        """Setup a dictionaries of source files"""
        value_tree_nodes: Dict[int, ValueTreeNode] = {}
        meta_node = SourceFile()
        sys.stdout.flush()
        for source_file in progressbar.progressbar(source_files):
            node = _generateValueTree(meta_node)
            meta_node.configureValueTree(node, source_file=source_file)
            value_tree_nodes[source_file.id_] = node
        return value_tree_nodes

    def setupSourceFiles(self, document: ValueTreeNode):
        """Setup a dictionaries of source files"""
        old_value_tree_nodes = MetaDocument._setupSourceFilesDict(
            "old", self.binary_pair.old_binary.source_files.values()
        )
        document.files.input.old.source_files = old_value_tree_nodes

        new_value_tree_nodes = MetaDocument._setupSourceFilesDict(
            "new", self.binary_pair.new_binary.source_files.values()
        )
        document.files.input.new.source_files = new_value_tree_nodes

    def configureValueTree(self, value_tree_node: ValueTreeNode, **kwargs: Any) -> None:
        """Configure the values of the document based on the information available
        from the settings
        """
        settings: Settings = kwargs["settings"]
        document = value_tree_node

        _validateSettings(settings)
        binary_pair_settings = BinaryPairSettings(
            short_name="",
            old_binary_filename=settings.old_binary_filename,
            new_binary_filename=settings.new_binary_filename,
        )
        self.binary_pair = BinaryPair(
            settings=settings, pair_settings=binary_pair_settings
        )

        old_binary: Binary = self.binary_pair.old_binary
        new_binary: Binary = self.binary_pair.new_binary

        if settings.project_title:
            doc_title: str = settings.project_title
        else:
            doc_title = "ELF Binary Comparison"

        persisting_symbols_overall_size_difference = 0
        persisting_symbols_overall_size_old = 0
        persisting_symbols_overall_size_new = 0

        for symbol_name in self.binary_pair.persisting_symbol_names:
            old_symbol: ElfSymbol = old_binary.symbols[symbol_name]
            new_symbol: ElfSymbol = new_binary.symbols[symbol_name]

            size_difference: int = new_symbol.size - old_symbol.size

            if (size_difference == 0) and settings.consider_equal_sized_identical:
                continue

            persisting_symbols_overall_size_old += old_symbol.size
            persisting_symbols_overall_size_new += new_symbol.size
            persisting_symbols_overall_size_difference += size_difference

        symbol_selection_regex_old: str = settings.symbol_selection_regex_old or ".*"
        symbol_selection_regex_new: str = settings.symbol_selection_regex_new or ".*"

        symbol_exclusion_regex_old: str = settings.symbol_exclusion_regex_old or ""
        symbol_exclusion_regex_new: str = settings.symbol_exclusion_regex_new or ""

        display_build_info = True
        if settings.build_info == "":
            display_build_info = False

        document.build_info = settings.build_info
        document.configuration.instructions_available = (
            self.binary_pair.old_binary.instructions_available
            and self.binary_pair.new_binary.instructions_available
        )
        document.configuration.display_binary_details = (
            settings.old_binary_info != ""
        ) or (settings.new_binary_info != "")
        document.configuration.display_build_info = display_build_info
        document.configuration.display_details = not settings.skip_details
        document.configuration.display_disappeared_symbols_overview = True
        document.configuration.display_new_binary_info = settings.new_binary_info != ""
        document.configuration.display_appeared_symbols_overview = True
        document.configuration.display_old_binary_info = settings.old_binary_info != ""
        document.configuration.display_persisting_symbols_overview = True
        document.configuration.display_similar_symbols = (
            not settings.skip_symbol_similarities
        )
        document.configuration.display_similar_symbols_overview = (
            not settings.skip_symbol_similarities
        )
        document.configuration.display_migrated_symbols = (
            self.binary_pair.debug_info_available
        )
        document.configuration.display_migrated_symbols_overview = (
            self.binary_pair.debug_info_available
        )
        document.files.input.old.binary_path = settings.old_alias
        document.files.input.new.binary_path = settings.new_alias
        document.files.input.old.debug_info_available = (
            self.binary_pair.old_binary.debug_info_available
        )
        document.files.input.new.debug_info_available = (
            self.binary_pair.new_binary.debug_info_available
        )
        document.general.doc_title = doc_title
        document.general.elf_diff_repo_root = settings.module_path
        document.general.generation_date = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        document.general.document_version = ELF_DIFF_DOCUMENT_VERSION
        document.general.page_title = "ELF Binary Comparison - (c) 2021 by noseglasses"
        document.general.elf_diff_version = gitRepoInfo(settings)
        document.new_binary_info = settings.new_binary_info
        document.old_binary_info = settings.old_binary_info
        document.statistics.overall.delta.resource_consumption.bss = (
            new_binary.symbol_sizes.bss_size - old_binary.symbol_sizes.bss_size
        )
        document.statistics.overall.delta.resource_consumption.code = (
            new_binary.symbol_sizes.progmem_size - old_binary.symbol_sizes.progmem_size
        )
        document.statistics.overall.delta.resource_consumption.data = (
            new_binary.symbol_sizes.data_size - old_binary.symbol_sizes.data_size
        )
        document.statistics.overall.delta.resource_consumption.static_ram = (
            new_binary.symbol_sizes.static_ram_size
            - old_binary.symbol_sizes.static_ram_size
        )
        document.statistics.overall.delta.resource_consumption.text = (
            new_binary.symbol_sizes.text_size - old_binary.symbol_sizes.text_size
        )
        document.statistics.overall.new.resource_consumption.bss = (
            new_binary.symbol_sizes.bss_size
        )
        document.statistics.overall.new.resource_consumption.code = (
            new_binary.symbol_sizes.progmem_size
        )
        document.statistics.overall.new.resource_consumption.data = (
            new_binary.symbol_sizes.data_size
        )
        document.statistics.overall.new.resource_consumption.static_ram = (
            new_binary.symbol_sizes.static_ram_size
        )
        document.statistics.overall.new.resource_consumption.text = (
            new_binary.symbol_sizes.text_size
        )
        document.statistics.overall.old.resource_consumption.bss = (
            old_binary.symbol_sizes.bss_size
        )
        document.statistics.overall.old.resource_consumption.code = (
            old_binary.symbol_sizes.progmem_size
        )
        document.statistics.overall.old.resource_consumption.data = (
            old_binary.symbol_sizes.data_size
        )
        document.statistics.overall.old.resource_consumption.static_ram = (
            old_binary.symbol_sizes.static_ram_size
        )
        document.statistics.overall.old.resource_consumption.text = (
            old_binary.symbol_sizes.text_size
        )
        document.statistics.symbols.appeared.count = (
            self.binary_pair.num_symbols_appeared
        )
        document.statistics.symbols.disappeared.count = (
            self.binary_pair.num_symbols_disappeared
        )
        document.statistics.symbols.new.count.dropped = new_binary.num_symbols_dropped
        document.statistics.symbols.new.count.selected = len(new_binary.symbols.keys())
        document.statistics.symbols.new.count.total = (
            document.statistics.symbols.new.count.dropped
            + document.statistics.symbols.new.count.selected
        )
        document.statistics.symbols.new.regex.exclusion = symbol_exclusion_regex_new
        document.statistics.symbols.new.regex.selection = symbol_selection_regex_new
        document.statistics.symbols.old.count.dropped = old_binary.num_symbols_dropped
        document.statistics.symbols.old.count.selected = len(old_binary.symbols.keys())
        document.statistics.symbols.old.count.total = (
            document.statistics.symbols.old.count.dropped
            + document.statistics.symbols.old.count.selected
        )
        document.statistics.symbols.old.regex.exclusion = symbol_exclusion_regex_old
        document.statistics.symbols.old.regex.selection = symbol_selection_regex_old
        document.statistics.symbols.persisting.count = len(
            self.binary_pair.persisting_symbol_names
        )
        document.statistics.symbols.persisting.resource_consumption.delta = (
            persisting_symbols_overall_size_difference
        )
        document.statistics.symbols.persisting.resource_consumption.old = (
            persisting_symbols_overall_size_old
        )
        document.statistics.symbols.persisting.resource_consumption.new = (
            persisting_symbols_overall_size_new
        )
        document.statistics.symbols.similar.count = len(
            self.binary_pair.similar_symbols
        )

        self.setupOldSymbolsDict(document, settings)
        self.setupNewSymbolsDict(document, settings)

        self.setupAppearedSymbolsDict(document, settings)
        self.setupDisappearedSymbolsDict(document, settings)
        self.setupPersistingSymbolsDict(document, settings)
        self.setupSimilarSymbolsDict(document, settings)
        self.setupMigratedSymbolsDict(document, settings)

        self.setupSourceFiles(document)


def generateDocumentTree() -> ValueTreeNode:
    """Generate a document tree (without symbols) and return its value tree"""
    meta_document = MetaDocument()
    value_tree = _generateValueTree(meta_document)
    return value_tree


def generateDocument(settings: Settings) -> ValueTreeNode:
    """Generate a document and return its value tree"""
    meta_document = MetaDocument()
    value_tree = _generateValueTree(meta_document)
    meta_document.configureValueTree(value_tree, settings=settings)
    return value_tree


def getDocumentTreesOfDynamicTreeNodes():
    """Returns a list that contains the meta tree nodes of all available symbol types (old/new/appeared/disappeared/persisting/similar)"""
    tree_dumps: Dict[str, SymbolType] = {}
    node_types = [SourceFile]
    node_types += SYMBOL_TYPES
    for node_type in node_types:
        symbol_entity_meta: SymbolType = node_type()
        symbol_entity_value = _generateValueTree(symbol_entity_meta)
        tree_dumps[node_type.__name__] = symbol_entity_value
    return tree_dumps
