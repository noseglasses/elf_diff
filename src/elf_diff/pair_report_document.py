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
# The leaf nodes of the value tree represent the values that can be used when rendering
# documents, e.g. as document.statistics.overall.new.resource_consumption.text
#
# The nodes of the meta tree store information about what is stored, e.g. the data types
# their documentation and means of validating the corresponding value tree nodes.
#
# The meta tree is established based on raw trees that are represented by nested dictionary objects.
# The raw tree is a nested tree structure where every node can either contain named subnodes or
# properties whose names start with an underscore.

from elf_diff.error_handling import unrecoverableError
from elf_diff.binary_pair import BinaryPair
from elf_diff.git import gitRepoInfo
import elf_diff.string_diff as string_diff
import copy
import datetime
import sys
import progressbar


def typeName(obj):
    """Returns the (shortest possible) type name of an object"""
    return type(obj).__name__


def incIndent(indent):
    """Increase the indentation based on an already present indentation"""
    return f"{indent}   "


class ValueTreeNode(object):
    """A node of the tree that represents the document externally"""

    def __init__(self):
        self.attachMetaTreeNode(None)

    def __getattr__(self, name):
        """An overloaded attribute getter method that helps with error reporting
        when developing Jinja templates.

        name: The name of the member to be accessed.
        """
        if name not in self.__dict__.keys():
            # print("Members available")
            # for key in self.__dict__.keys():
            #    print("   %s" % key)
            unrecoverableError(
                "Tree node %s does not have a member '%s'" % (self.getPath(), name)
            )
        return self.__dict__[name]

    def __setattr__(self, name, value):
        """An overloaded attribute setter method that takes care of notifying the associated
        meta tree node of the value update.
        """
        super().__setattr__(name, value)
        self.metaTreeNode().notifyAttributeAssigned(name, value)

    def attachMetaTreeNode(self, value_tree_node):
        self.__dict__[
            "_m"
        ] = value_tree_node  # Not using setattr(...) prevents __setattr__ being invoked

    def addChild(self, name, value):
        self.__dict__[name] = value

    def metaTreeNode(self):
        return self.__dict__["_m"]

    def getPath(self):
        return self.metaTreeNode().getPath()


# Allowed meta attributes
# The dict values are validator functors that are used to check if a
# meta attribute is specified with correct type.
ALLOWED_RAW_TREE_PROPERTIES = {
    "_doc": lambda value: isinstance(value, str) or (value is None) or callable(value),
    "_type": lambda value: value in (str, bool, int, float),
    "_alias_type": lambda value: value is str,
    "_validator": callable,
    "_value_printer": callable,
}


def isRawTreeProperty(key):
    return isinstance(key, str) and (key in ALLOWED_RAW_TREE_PROPERTIES.keys())


def isRawTreePropertyValid(key, value):
    return ALLOWED_RAW_TREE_PROPERTIES[key](value)


def collectRawTreeProperties(raw_tree):
    raw_tree_properties = {}
    for attribute in ALLOWED_RAW_TREE_PROPERTIES.keys():
        if attribute in raw_tree.keys():
            raw_tree_properties[attribute] = raw_tree[attribute]
    return raw_tree_properties


class RawTreeValidator(object):
    def __init__(self, node, raw_tree):
        self.node = node
        self.raw_tree = raw_tree
        self.child_node_names_encountered = set()

    def checkChildName(self, key):
        if key in self.child_node_names_encountered:
            unrecoverableError(
                "Child name %s ambiguously defined in raw tree of node %s"
                % (key, self.node.getPath())
            )
        self.child_node_names_encountered.add(key)

    def validate(self):
        for key, value in self.raw_tree.items():
            if isRawTreeProperty(key):
                if not isRawTreePropertyValid(key, value):
                    unrecoverableError(
                        "Invalid raw tree property (type) %s of %s"
                        % (key, self.node.getPath())
                    )

            if isinstance(key, tuple):
                for tuple_entry in key:
                    self.checkChildName(tuple_entry)
            else:
                self.checkChildName(key)


def generateMetaTreeNode(raw_tree, raw_tree_properties=None):
    # The meta tree node type may be explicitly defined as a raw tree property.
    # This is important to enable raw trees being nested and
    # the nested raw trees be represented by a separate custom meta
    # tree node class. In that case the property _node_type
    # must be used to define the type of the node that is
    # to be instanciated.
    if "_node_type" in raw_tree.keys():
        node_type = raw_tree["_node_type"]
        new_node = node_type(raw_tree_properties)  # Call meta tree node constructor
    elif isRawTreeLeafNode(raw_tree):
        new_node = MetaTreeLeafNode(raw_tree, raw_tree_properties)
    else:
        new_node = MetaTreeInteriorNode(raw_tree, raw_tree_properties)

    return new_node


def isRawTreeMultiNode(key):
    """
    Checks if a raw tree node is a multi-node.
    Multi nodes are raw tree nodes that
    define a set of independent identical meta tree subtrees
    with different names. The names of the subtrees
    are provided as a tuple datatype.
    """
    return isinstance(key, tuple)


def isRawTreeLeafNode(raw_tree):
    # Check if the node does only contain meta attributes
    for key in raw_tree.keys():
        if isRawTreeMultiNode(key):
            # Multi nodes define subtrees. Therefore this is not a leaf node.
            return False
        if not isRawTreeProperty(key):
            # Anything else that is not a property is also a subtree and therefore this can also not be a leaf node.
            return False
    return True


class MetaTreeNodeBase(object):
    """A common base class for all meta tree node types"""

    def __init__(self, raw_tree, raw_tree_properties):
        self._name = None
        self._raw_tree = raw_tree
        self._raw_tree_properties = raw_tree_properties
        self._parent = None

        # Generate a parallel tree structure only for the values
        self._v = ValueTreeNode()
        self._v.attachMetaTreeNode(self)

        self.setupFromRawTree()

    def unrecoverableError(self, what):
        unrecoverableError(
            "Meta tree node %s %s: %s" % (typeName(self), self.getPath(), what)
        )

    def getValueTree(self):
        return self._v

    def getPath(self):
        if self._parent is not None:
            return "%s.%s" % (self._parent.getPath(), self._name)
        return self._name

    def setParent(self, parent):
        self._parent = parent

    def assertMetaArgsDefined(self, args_list):
        for meta_arg in args_list:
            if meta_arg not in self._raw_tree_properties.keys():
                self.unrecoverableError("Lacking meta attribute %s" % meta_arg)

    def validate(self):
        if "_validator" in self._raw_tree_properties.keys():
            if self._raw_tree_properties["_validator"](self) is False:
                self.unrecoverableError("Validation failed")

    def formatDocString(self):
        self.assertMetaArgsDefined(["_doc"])

        if callable(self._raw_tree_properties["_doc"]):
            doc_callable = self._raw_tree_properties["_doc"]
            doc_string = doc_callable(self)
        else:
            doc_string = self._raw_tree_properties["_doc"]

        if doc_string is not None:
            formatted_doc_string = " [%s]" % doc_string
        else:
            formatted_doc_string = ""

        return formatted_doc_string


class MetaTreeInteriorNode(MetaTreeNodeBase):
    def __init__(self, raw_tree, raw_tree_properties):
        self._children = {}
        self.is_leaf = False
        super().__init__(raw_tree, raw_tree_properties)

    def inheritMetaAttributes(self, child_raw_tree):
        child_raw_tree_properties = copy.deepcopy(self._raw_tree_properties)

        # Inherit attributes
        for meta_attribute in ALLOWED_RAW_TREE_PROPERTIES.keys():
            if meta_attribute in child_raw_tree.keys():
                child_raw_tree_properties[meta_attribute] = child_raw_tree[
                    meta_attribute
                ]

        return child_raw_tree_properties

    def setupFromRawTree(self):
        # Initializes the node base on the raw tree

        # Process child nodes
        for key, child_raw_tree in self._raw_tree.items():

            # Ignore meta attributes
            if isRawTreeProperty(key):
                continue

            child_raw_tree_properties = self.inheritMetaAttributes(child_raw_tree)

            if isRawTreeMultiNode(key):
                for sibling in key:
                    child_node = generateMetaTreeNode(
                        child_raw_tree, child_raw_tree_properties
                    )
                    child_node._name = sibling
                    self.addChild(child_node)
                continue

            if isinstance(child_raw_tree, str):
                self.unrecoverableError(
                    "Strange subnode %s = %s" % (key, child_raw_tree)
                )

            child_node = generateMetaTreeNode(child_raw_tree, child_raw_tree_properties)
            child_node._name = key

            self.addChild(child_node)

    def addChild(self, child):
        child.setParent(self)
        self._children[child._name] = child
        self.getValueTree().addChild(child._name, child._v)

    def notifyAttributeAssigned(self, name, value):
        """Notification method called by the associated value tree node"""
        child = self._children[name]
        if not isinstance(child, MetaTreeLeafNode):
            self.unrecoverableError(
                "Attempted assignment to a non leaf value %s" % name
            )
        child._value = value

    def prettyPrint(self, display_values=True, name_alias=None):
        formatted_doc_string = self.formatDocString()
        name = name_alias or self._name
        return "%s%s" % (name, formatted_doc_string)

    def forEachChild(self, lambda_):
        for key in sorted(self._children):
            child = self._children[key]
            lambda_(self, child)

    def validateRawTree(self):
        tree_validator = RawTreeValidator(self, self._raw_tree)
        tree_validator.validate()

        # Make sure that any child meta tree nodes are also defined in the raw tree.
        for child_name in self._children.keys():
            if child_name not in tree_validator.child_node_names_encountered:
                self.unrecoverableError(
                    "Accidentally exports child node '%s' that is not present in the raw tree"
                    % child_name
                )

    def validate(self):
        super().validate()

        self.validateRawTree()

        # Recursively validate children
        self.forEachChild(lambda parent, child: child.validate())


class MetaTreeLeafNode(MetaTreeNodeBase):
    def __init__(self, raw_tree, raw_tree_properties):
        super().__init__(raw_tree, raw_tree_properties)
        self._value = None
        self.is_leaf = True

    def __setattr__(self, name, value):
        if name == "_value":
            if isinstance(value, dict):
                self.is_leaf = False
        self.__dict__[name] = value

    def setupFromRawTree(self):
        pass

    def validate(self):
        if self._value is None:
            self.unrecoverableError("Value yet unset")
        if ("_type" in self._raw_tree_properties.keys()) and (
            not isinstance(self._value, self._raw_tree_properties["_type"])
        ):
            self.unrecoverableError(
                "Value type mismatch: Expected %s, obtained %s"
                % (str(self._raw_tree_properties["_type"]), str(type(self._value)))
            )
        super().validate()

    def prettyPrint(self, display_values=True, name_alias=None):
        formatted_doc_string = self.formatDocString()

        if display_values and (not isinstance(self._value, dict)):
            if "_value_printer" in self._raw_tree_properties.keys():
                actual_value = self._raw_tree_properties["_value_printer"](self._value)
            else:
                actual_value = self._value
            formatted_value = " = '%s'" % actual_value
            type_info = " <%s>" % typeName(self._value)
        else:
            formatted_value = ""
            if "_alias_type" in self._raw_tree_properties.keys():
                type_info = " <%s>" % self._raw_tree_properties["_alias_type"]
            elif "_type" in self._raw_tree_properties.keys():
                type_info = " <%s>" % self._raw_tree_properties["_type"].__name__
            else:
                type_info = ""

        name = name_alias or self._name

        return "%s%s%s%s" % (name, formatted_value, type_info, formatted_doc_string)

    def renderPaths(self):
        print(self.getPath())

    def generateValueTree(self):
        return self._value


class CustomMetaTreeInteriorNode(MetaTreeInteriorNode):
    def __init__(self, raw_tree_properties=None):
        raw_tree = self.getRawTree()
        if raw_tree_properties is None:
            raw_tree_properties = collectRawTreeProperties(raw_tree)
        # Custom types must feature a class dict tree
        # raw_tree is replaced by the node's own tree
        super().__init__(raw_tree, raw_tree_properties)

    def getRawTree(self):
        return type(self).RAW_TREE


class Symbol(CustomMetaTreeInteriorNode):
    RAW_TREE = {
        "_doc": None,
        "name": {"_doc": "The symbol name (demangled if supported)", "_type": str},
        "is_demangled": {
            "_doc": "True if the symbol name is demangled",
            "_type": bool,
        },
        "type": {
            "_doc": "Type character matching the characters used by the nm binutils tool",
            "_type": str,
        },
        "id": {"_doc": "Unique symbol identifier", "_type": int},
        "size": {"_doc": "Number of bytes occupied by the symbol", "_type": int},
        "instructions": {
            "_doc": "Code instructions (assembly with possibly high level language code intermixed)",
            "_type": str,
        },
        "is_stored_in_program_memory": {
            "_doc": "True if the symbol is stored in program memory",
            "_type": bool,
        },
    }

    def __init__(self, raw_tree_properties=None):
        super().__init__(raw_tree_properties)
        self._name = "symbol"

    def configureValues(self, symbol):
        node = self.getValueTree()
        node.name = symbol.name
        node.is_demangled = symbol.is_demangled
        node.type = symbol.type_
        node.id = symbol.id_
        node.size = symbol.size
        node.instructions = symbol.instructions
        node.is_stored_in_program_memory = symbol.livesInProgramMemory()


class DisplayInfo(CustomMetaTreeInteriorNode):
    RAW_TREE = {
        "_doc": "Information that configures how things are displayed",
        "symbol_class": {
            "_doc": "The class of symbol old/new/appeared/disappeared/persisting/similar",
            "_type": str,
        },
        "anchor_id": {
            "_doc": "Unique string identifier token that can be used to generate a HTML anchor for cross references",
            "_type": str,
        },
        "display_symbol_details": {
            "_doc": "True if symbol details are supposed to be displayed",
            "_type": bool,
        },
    }

    def configureValues(self, settings, symbol_class, symbol1, symbol2=None):

        if symbol2 is None:
            symbol2 = symbol1

        if (
            (symbol1.symbol_type == symbol1.type_data)
            or (not symbol1.hasInstructions())
            or (not symbol2.hasInstructions())
        ):
            display_symbol_details = False
        else:
            display_symbol_details = True

        node = self.getValueTree()
        node.symbol_class = symbol_class
        node.anchor_id = str(symbol1.id_)
        node.display_symbol_details = display_symbol_details


class RelatedSymbols(CustomMetaTreeInteriorNode):
    RAW_TREE = {
        "_doc": "A relation between two symbols",
        "size_delta": {
            "_doc": "Difference in bytes between the resource occupation of the two symbols",
            "_type": int,
        },
        "old": {
            "_doc": "The old symbol",
            "_type": ValueTreeNode,
            "_alias_type": Symbol.__name__,
        },
        "new": {
            "_doc": "The new symbol",
            "_type": ValueTreeNode,
            "_alias_type": Symbol.__name__,
        },
    }

    def configureValues(self, old_symbol, new_symbol):
        node = self.getValueTree()
        node.size_delta = new_symbol.size - old_symbol.size
        node.old = old_symbol.jinja_tree_node
        node.new = new_symbol.jinja_tree_node


class IsolatedSymbol(CustomMetaTreeInteriorNode):
    RAW_TREE = {
        "_doc": None,
        "display_info": {"_doc": "The display info", "_node_type": DisplayInfo},
        "actual": {
            "_doc": "The actual symbol",
            "_type": ValueTreeNode,
            "_alias_type": Symbol.__name__,
            "_value_printer": lambda value: value.id,
        },
    }

    def __init__(self, raw_tree_properties=None):
        super().__init__(raw_tree_properties)
        self._name = f"{self.SYMBOL_CLASS}_symbol"

    def configureValues(self, settings, symbol):
        self._children["display_info"].configureValues(
            settings=settings, symbol_class=self.SYMBOL_CLASS, symbol1=symbol
        )

        node = self.getValueTree()
        node.actual = symbol.jinja_tree_node


class AppearedSymbol(IsolatedSymbol):
    SYMBOL_CLASS = "appeared"


class DisappearedSymbol(IsolatedSymbol):
    SYMBOL_CLASS = "disappeared"


class PersistingSymbol(CustomMetaTreeInteriorNode):
    RAW_TREE = {
        "_doc": None,
        "display_info": {"_node_type": DisplayInfo},
        "related_symbols": {"_node_type": RelatedSymbols},
    }

    def __init__(self, raw_tree_properties=None):
        super().__init__(raw_tree_properties)
        self._name = "persisting_symbol"

    def configureValues(self, settings, old_symbol, new_symbol):
        self._children["display_info"].configureValues(
            settings=settings,
            symbol_class="persisting",
            symbol1=old_symbol,
            symbol2=new_symbol,
        )
        self._children["related_symbols"].configureValues(old_symbol, new_symbol)


class SimilarSymbols(CustomMetaTreeInteriorNode):

    RAW_TREE = {
        "_doc": None,
        "display_info": {"_node_type": DisplayInfo},
        "related_symbols": {"_node_type": RelatedSymbols},
        "id": {"_doc": "The id of the symbol pair", "_type": int},
        ("old", "new"): {
            "signature_tagged": {
                "_doc": "A tagged version of the symbol signature. Taggs '%s' and '%s' must be replaced accordingly, e.g. for highlighting."
                % (string_diff.HIGHLIGHT_START_TAG, string_diff.HIGHLIGHT_END_TAG),
                "_type": str,
            }
        },
        "similarities": {
            "_doc": "Symbol similarity ratios",
            "_type": float,
            "signature": {"_doc": "The percentage of symbol signature similarity"},
            "instruction": {"_doc": "The percentage of symbol instruction similarity"},
        },
    }

    def __init__(self, raw_tree_properties=None):
        super().__init__(raw_tree_properties)
        self._name = "similar_symbols"

    def configureValues(self, settings, symbol_pair, id_):
        instruction_similarity = 1.0
        if symbol_pair.instruction_similarity is not None:
            instruction_similarity = symbol_pair.instruction_similarity * 100.0

        self._children["display_info"].configureValues(
            settings=settings,
            symbol_class="similar",
            symbol1=symbol_pair.old_symbol,
            symbol2=symbol_pair.new_symbol,
        )
        self._children["related_symbols"].configureValues(
            symbol_pair.old_symbol, symbol_pair.new_symbol
        )

        node = self.getValueTree()
        node.id = id_
        node.old.signature_tagged = string_diff.tagStringDiffSource(
            symbol_pair.old_symbol.name, symbol_pair.new_symbol.name
        )
        node.new.signature_tagged = string_diff.tagStringDiffTarget(
            symbol_pair.old_symbol.name, symbol_pair.new_symbol.name
        )
        node.similarities.signature = symbol_pair.signature_similarity * 100.0
        node.similarities.instruction = instruction_similarity


SYMBOL_TYPES = (
    Symbol,
    PersistingSymbol,
    AppearedSymbol,
    DisappearedSymbol,
    SimilarSymbols,
)


def assertAllDictValueMembersAreInstance(node, type_):
    if not isinstance(node._value, dict):
        node.unrecoverableError("Expected value type dict")

    for key, value in node._value.items():
        if not isinstance(value, type_):
            node.unrecoverableError(
                "Dict member type validation failed. id: %s, expected node type: %s, actual: %s"
                % (key, type_.__name__, typeName(value))
            )
    return True


class MetaDocument(CustomMetaTreeInteriorNode):
    resource_consumption = {
        "_doc": "Information about resource consumption",
        "_type": int,
        "code": {"_doc": "Memory required to store code"},
        "static_ram": {"_doc": "Static RAM consumption"},
        "text": {"_doc": "text section memory consumption"},
        "data": {"_doc": "data section memory consumption"},
        "bss": {"_doc": "bss section memory consumption"},
    }
    RAW_TREE = {
        "general": {
            "_doc": "General information about the document",
            "page_title": {"_doc": "The title of the document page", "_type": str},
            "doc_title": {"_doc": "Document title", "_type": str},
            "elf_diff_repo_root": {
                "_doc": "Path to the root of the elf_diff git repo",
                "_type": str,
            },
            "generation_date": {"_doc": "The document generation date", "_type": str},
            "elf_diff_version": {
                "_doc": "The elf_diff version that generated the page",
                "_type": str,
            },
        },
        "configuration": {
            "_doc": "Boolean flags that configure what is supposed to be displayed and how",
            "_type": bool,
            "instructions_available": {
                "_doc": "True if instructions could be read from both binary files"
            },
            "display_old_binary_info": {
                "_doc": "True if old binary info is supposed to be displayed"
            },
            "display_new_binary_info": {
                "_doc": "True if new binary info is supposed to be displayed"
            },
            "display_details": {
                "_doc": "True if symbol detail information is supposed to be displayed"
            },
            "display_binary_details": {
                "_doc": "True if details about binaries are supposed to be displayed"
            },
            "display_build_info": {
                "_doc": "True if build information is supposed to be displayed"
            },
            "display_persisting_symbols_overview": {
                "_doc": "True if an overview about persisting symbols is supposed to be displayed"
            },
            "display_disappeared_symbols_overview": {
                "_doc": "True if an overview about disappeared symbols is supposed to be displayed"
            },
            "display_appeared_symbols_overview": {
                "_doc": "True if an overview about appeared symbols is supposed to be displayed"
            },
            "display_similar_symbols_overview": {
                "_doc": "True if an overview about similar symbols is supposed to be displayed"
            },
            "display_similar_symbols": {
                "_doc": "True if similar symbols are supposed to be displayed"
            },
        },
        "old_binary_info": {"_doc": "Info about the old binary", "_type": str},
        "new_binary_info": {"_doc": "Info about the new binary", "_type": str},
        "build_info": {"_doc": "Information about the build", "_type": str},
        "files": {
            "_doc": "Information about relevant files",
            "input": {
                "_doc": "Information about relevant input files",
                ("old", "new"): {
                    "binary_path": {"_doc": "The path to the binary file", "_type": str}
                },
            },
        },
        "statistics": {
            "_doc": None,
            "overall": {
                "_doc": "Overall statistics",
                ("old", "new", "delta"): {
                    "_doc": None,
                    "resource_consumption": resource_consumption,
                },
            },
            "symbols": {
                "_doc": "Statistics of symbols",
                ("old", "new"): {
                    "_doc": "Overall statistics about symbols considered",
                    "count": {
                        "_doc": "Number of symbols",
                        "selected": {
                            "_doc": "Number of symbols selected",
                            "_type": int,
                        },
                        "dropped": {"_doc": "Number of symbols dropped", "_type": int},
                        "total": {
                            "_doc": "Number of total symbols in binary",
                            "_type": int,
                        },
                    },
                    "regex": {
                        "selection": {
                            "_doc": "Regular expression used to select symbols found in binary",
                            "_type": str,
                        },
                        "exclusion": {
                            "_doc": "Regular expression used to exclude symbols found in binary",
                            "_type": str,
                        },
                    },
                },
                ("appeared", "disappeared"): {
                    "_doc": None,
                    "count": {"_doc": "Number of symbols", "_type": int},
                },
                "persisting": {
                    "_doc": None,
                    "count": {"_doc": "Number of symbols", "_type": int},
                    "resource_consumption": {
                        "_doc": "Total resource consumption of considered symbols of given class",
                        "old": {
                            "_doc": "Overall number of bytes consumed in the old version",
                            "_type": int,
                        },
                        "new": {
                            "_doc": "Overall number of bytes consumed in the old version",
                            "_type": int,
                        },
                        "delta": {
                            "_doc": "Change to number of bytes consumed (only for persisting and similar)",
                            "_type": int,
                        },
                    },
                },
                "similar": {
                    "_doc": None,
                    "count": {"_doc": "Number of symbols", "_type": int},
                },
            },
        },
        "symbols": {
            "_doc": "Symbols by id/table id ",
            "old": {
                "_doc": "Dict of selected symbols of the old binary by symbol id (dict values of type Symbol)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, Symbol
                ),
            },
            "new": {
                "_doc": "Dict of selected symbols of the new binary by symbol id (dict values of type Symbol)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, Symbol
                ),
            },
            "appeared": {
                "_doc": "Dict of appeared symbols by symbol id (dict values of type AppearedSymbol)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, AppearedSymbol
                ),
            },
            "disappeared": {
                "_doc": "Disappeared symbols by symbol id (dict values of type DisappearedSymbol)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, DisappearedSymbol
                ),
            },
            "persisting": {
                "_doc": "Persisting symbols by symbol id (dict values of type PersistingSymbol)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, PersistingSymbol
                ),
            },
            "similar": {
                "_doc": "Similar symbols by symbol id (dict values of type SimilarSymbols)",
                "_validator": lambda node: assertAllDictValueMembersAreInstance(
                    node, SimilarSymbols
                ),
            },
        },
    }

    def __init__(self):
        super().__init__({"_doc": None})
        self._name = "document"

    def validateSettings(self):
        if not self.settings.old_binary_filename:
            unrecoverableError("No old binary filename defined")

        if not self.settings.new_binary_filename:
            unrecoverableError("No new binary filename defined")

    def registerSymbolNodes(self, nodes_list, symbol_class, id_getter):
        value_raw_tree = {}
        meta_raw_tree = {}
        for node in nodes_list:
            node.validate()
            id_ = id_getter(node)
            value_raw_tree[id_] = node._v
            meta_raw_tree[id_] = node
        symbol_class_location = getattr(self.getValueTree().symbols, symbol_class)

        # Important: First set the dict value in the value tree node, then the meta tree dict.
        #            Otherwise setting the value tree dict second would override the previously
        #            set meta tree dict due to the notifyAttributeAssigned notification
        #            being called.
        setattr(self.getValueTree().symbols, symbol_class, value_raw_tree)
        setattr(symbol_class_location._m, "_value", meta_raw_tree)

    def setupSymbolsDict(self, symbols, symbol_class):
        nodes = []
        print(f"Adding {symbol_class} symbols to document")
        sys.stdout.flush()
        for symbol in progressbar.progressbar(symbols):
            node = Symbol()
            node._name = "%s_symbol" % symbol_class
            node.configureValues(symbol)
            symbol.jinja_tree_node = (
                node.getValueTree()
            )  # Make the jinja tree node available directly
            nodes.append(node)

        def getId(node):
            return node.getValueTree().id

        self.registerSymbolNodes(nodes, symbol_class, getId)

    def setupOldSymbolsDict(self):
        self.setupSymbolsDict(self.binary_pair.old_binary.symbols.values(), "old")

    def setupNewSymbolsDict(self):
        self.setupSymbolsDict(self.binary_pair.new_binary.symbols.values(), "new")

    def setupPersistingSymbolsDict(self):
        nodes = []
        print("Adding persisting symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.persisting_symbol_names
        ):

            old_symbol = self.binary_pair.old_binary.symbols[symbol_name]
            new_symbol = self.binary_pair.new_binary.symbols[symbol_name]

            node = PersistingSymbol()
            node.configureValues(
                settings=self.settings, old_symbol=old_symbol, new_symbol=new_symbol
            )
            node._name = "persisting_symbol"
            nodes.append(node)

        def getId(node):
            return node.getValueTree().related_symbols.old.id

        self.registerSymbolNodes(nodes, "persisting", getId)

    def setupAppearedSymbolsDict(self):
        nodes = []
        print("Adding appeared symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.appeared_symbol_names
        ):
            appeared_symbol = self.binary_pair.new_binary.symbols[symbol_name]
            node = AppearedSymbol()
            node._name = "appeared_symbol"
            node.configureValues(settings=self.settings, symbol=appeared_symbol)
            nodes.append(node)

        def getId(node):
            return node.getValueTree().actual.id

        self.registerSymbolNodes(nodes, "appeared", getId)

    def setupDisappearedSymbolsDict(self):
        nodes = []
        print("Adding disappeared symbols to document")
        sys.stdout.flush()
        for symbol_name in progressbar.progressbar(
            self.binary_pair.disappeared_symbol_names
        ):
            disappeared_symbol = self.binary_pair.old_binary.symbols[symbol_name]
            node = DisappearedSymbol()
            node._name = "disappeared_symbol"
            node.configureValues(settings=self.settings, symbol=disappeared_symbol)
            nodes.append(node)

        def getId(node):
            return node.getValueTree().actual.id

        self.registerSymbolNodes(nodes, "disappeared", getId)

    def setupSimilarSymbolsDict(self):
        nodes = []
        id_ = 0
        print("Adding similar symbols to document")
        sys.stdout.flush()
        for i in progressbar.progressbar(range(len(self.binary_pair.similar_symbols))):
            symbol_pair = self.binary_pair.similar_symbols[i]
            node = SimilarSymbols()
            node._name = "similar_symbols"
            node.configureValues(
                settings=self.settings, symbol_pair=symbol_pair, id_=id_
            )
            nodes.append(node)
            id_ += 1

        def getId(node):
            return node.getValueTree().id

        self.registerSymbolNodes(nodes, "similar", getId)

    def configureValues(self, settings):

        self.settings = settings

        self.validateSettings()

        self.binary_pair = BinaryPair(
            settings, settings.old_binary_filename, settings.new_binary_filename
        )

        old_binary = self.binary_pair.old_binary
        new_binary = self.binary_pair.new_binary

        if self.settings.project_title:
            doc_title = self.settings.project_title
        else:
            doc_title = "ELF Binary Comparison"

        persisting_symbols_overall_size_difference = 0
        persisting_symbols_overall_size_old = 0
        persisting_symbols_overall_size_new = 0

        for symbol_name in self.binary_pair.persisting_symbol_names:
            old_symbol = old_binary.symbols[symbol_name]
            new_symbol = new_binary.symbols[symbol_name]

            size_difference = new_symbol.size - old_symbol.size

            if (size_difference == 0) and self.settings.consider_equal_sized_identical:
                continue

            persisting_symbols_overall_size_old += old_symbol.size
            persisting_symbols_overall_size_new += new_symbol.size
            persisting_symbols_overall_size_difference += size_difference

        symbol_selection_regex_old = ".*"
        if old_binary.symbol_selection_regex is not None:
            symbol_selection_regex_old = old_binary.symbol_selection_regex

        symbol_selection_regex_new = ".*"
        if new_binary.symbol_selection_regex is not None:
            symbol_selection_regex_new = new_binary.symbol_selection_regex

        symbol_exclusion_regex_old = ""
        if old_binary.symbol_exclusion_regex is not None:
            symbol_exclusion_regex_old = old_binary.symbol_exclusion_regex

        symbol_exclusion_regex_new = ""
        if new_binary.symbol_exclusion_regex is not None:
            symbol_exclusion_regex_new = new_binary.symbol_exclusion_regex

        display_build_info = True
        if self.settings.build_info == "":
            display_build_info = False

        document = self.getValueTree()
        document.build_info = self.settings.build_info
        document.configuration.instructions_available = (
            self.binary_pair.old_binary.instructions_available
            and self.binary_pair.new_binary.instructions_available
        )
        document.configuration.display_binary_details = (
            self.settings.old_binary_info != ""
        ) or (self.settings.new_binary_info != "")
        document.configuration.display_build_info = display_build_info
        document.configuration.display_details = not self.settings.skip_details
        document.configuration.display_disappeared_symbols_overview = True
        document.configuration.display_new_binary_info = (
            self.settings.new_binary_info != ""
        )
        document.configuration.display_appeared_symbols_overview = True
        document.configuration.display_old_binary_info = (
            self.settings.old_binary_info != ""
        )
        document.configuration.display_persisting_symbols_overview = True
        document.configuration.display_similar_symbols = (
            not self.settings.skip_symbol_similarities
        )
        document.configuration.display_similar_symbols_overview = (
            not self.settings.skip_symbol_similarities
        )
        document.files.input.new.binary_path = self.settings.new_alias
        document.files.input.old.binary_path = self.settings.old_alias
        document.general.doc_title = doc_title
        document.general.elf_diff_repo_root = self.settings.module_path
        document.general.generation_date = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        document.general.page_title = "ELF Binary Comparison - (c) 2021 by noseglasses"
        document.general.elf_diff_version = gitRepoInfo(self.settings)
        document.new_binary_info = self.settings.new_binary_info
        document.old_binary_info = self.settings.old_binary_info
        document.statistics.overall.delta.resource_consumption.bss = (
            new_binary.bss_size - old_binary.bss_size
        )
        document.statistics.overall.delta.resource_consumption.code = (
            new_binary.progmem_size - old_binary.progmem_size
        )
        document.statistics.overall.delta.resource_consumption.data = (
            new_binary.data_size - new_binary.data_size
        )
        document.statistics.overall.delta.resource_consumption.static_ram = (
            new_binary.static_ram_size - old_binary.static_ram_size
        )
        document.statistics.overall.delta.resource_consumption.text = (
            new_binary.text_size - old_binary.text_size
        )
        document.statistics.overall.new.resource_consumption.bss = new_binary.bss_size
        document.statistics.overall.new.resource_consumption.code = (
            new_binary.progmem_size
        )
        document.statistics.overall.new.resource_consumption.data = new_binary.data_size
        document.statistics.overall.new.resource_consumption.static_ram = (
            new_binary.static_ram_size
        )
        document.statistics.overall.new.resource_consumption.text = new_binary.text_size
        document.statistics.overall.old.resource_consumption.bss = old_binary.bss_size
        document.statistics.overall.old.resource_consumption.code = (
            old_binary.progmem_size
        )
        document.statistics.overall.old.resource_consumption.data = old_binary.data_size
        document.statistics.overall.old.resource_consumption.static_ram = (
            old_binary.static_ram_size
        )
        document.statistics.overall.old.resource_consumption.text = old_binary.text_size
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

        self.setupOldSymbolsDict()
        self.setupNewSymbolsDict()

        self.setupAppearedSymbolsDict()
        self.setupDisappearedSymbolsDict()
        self.setupPersistingSymbolsDict()
        self.setupSimilarSymbolsDict()

        self.validate()


def generateDocument(settings):
    meta_document = MetaDocument()
    meta_document.configureValues(settings)
    return meta_document.getValueTree()


def getDocumentTreesOfSymbolClasses():
    """Returns a list that contains the meta tree nodes of all available symbol types (old/new/appeared/disappeared/persisting/similar)"""
    tree_dumps = {}
    for symbol_type in SYMBOL_TYPES:
        symbol_entity = symbol_type()
        tree_dumps[symbol_type.__name__] = symbol_entity
    return tree_dumps
