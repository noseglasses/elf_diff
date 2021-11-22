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
from elf_diff.value_tree import ValueType
from elf_diff.value_tree import Value as ValueTreeValue
from elf_diff.settings import Settings
from elf_diff.pair_report_document import (
    ValueTreeNode,
    getDocumentTreesOfDynamicTreeNodes,
    generateDocumentTree,
)
from elf_diff.auxiliary import isNameToken
import anytree  # type: ignore # Make mypy ignore this module
import os
from typing import Optional, Dict, Union, Any, List, Tuple


def prettyPrintNode(
    value_tree_node: ValueTreeNode,
    display_values: bool = True,
    name_alias: Optional[str] = None,
) -> str:
    """Return a pretty printed version of the value tree node"""
    return "%s%s" % (value_tree_node.getName(), value_tree_node.getDocumentation())


def prettyPrintValue(
    value_tree_value: ValueTreeValue,
    display_values: bool = True,
    name_alias: Optional[str] = None,
) -> str:
    """Return a pretty printed version of the leaf node"""
    formatted_doc_string: str = value_tree_value.getDocumentation()

    if display_values and (not isinstance(value_tree_value._value, dict)):
        dynamic_value = value_tree_value.getValue()
        formatted_value: str = f" = '{dynamic_value}'"
        type_info: str = " <%s>" % value_tree_value.getType().__name__
    else:
        formatted_value = ""
        type_info = value_tree_value.getFormattedTypeInfo()

    name: str = name_alias or value_tree_value.getName()

    return "%s%s%s%s" % (name, formatted_value, type_info, formatted_doc_string)


def enforceNameStartsWithNameToken(name: Any) -> str:
    """Add a leading underscore if the name starts with a non-name character"""
    name_str = str(name)
    if not isNameToken(name_str[0]):
        return f"_{name_str}"
    return name_str


class TreeTraversalOptions(object):
    """Options that affect how document trees or subtrees are traversed"""

    def __init__(self, visit_dict_nodes: bool = True, visit_values: bool = True):
        self.visit_dict_nodes: bool = visit_dict_nodes
        self.visit_values: bool = visit_values


TREE_TRAVERSAL_ALL = TreeTraversalOptions(visit_dict_nodes=True, visit_values=True)


class GeneratorOptions(object):
    def __init__(self, enforce_names_alpha=True):
        self.enforce_names_alpha = enforce_names_alpha


class ValueTreeVisitor(object):
    """A base class of visitors that traverse the value tree"""

    def __init__(self, traversal_options: Optional[TreeTraversalOptions] = None):
        self.tree_traversal_options = traversal_options or TreeTraversalOptions()

    def visit(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        # Some nodes store reference to nodes that are already stored in other
        # places of the tree. Those references are stored in the _value
        # member of the Value class.
        #
        # This poses the problem which name to reference the node by,
        # the one of the reference or the one of the actual node.
        #
        # Here we decide for the reference as that is what we want to output
        # when rendering trees. To achieve this, we submit the name
        # of the node that holds the reference as an alias name.
        #
        # Important: In this special case, we don't want to call onDown and onUp
        #            as we want to replace the referencing node by the referenced
        #            node. Otherwise we would have both listed in the tree
        #            in an unwanted nested fashion.

        self._onDown(value_tree_node, **kvargs)

        attributes = value_tree_node.getValueAndChildAttributes()

        for name in sorted(attributes.keys()):
            attr_type = attributes[name]
            if attr_type == ValueTreeNode.VALUE_ATTRIBUTE:
                if not self.tree_traversal_options.visit_values:
                    continue
                value = value_tree_node.getValue(name)
                raw_value = value.getValue()
                if isinstance(raw_value, dict):
                    if self.tree_traversal_options.visit_dict_nodes:
                        dict_ = raw_value
                        self._beforeDict(value.getName(), dict_)
                        for id_ in sorted(dict_.keys()):
                            subtree = dict_[id_]
                            self._beforeDictEntry(id_, subtree)
                            self.visit(subtree, **kvargs)
                            self._afterDictEntry(id_, subtree)
                        self._afterDict(value.getName(), dict_)
                    else:
                        self._processValue(name, value)
                elif isinstance(raw_value, ValueTreeNode):
                    self.visit(raw_value, **kvargs)
                else:
                    self._processValue(name, value)
            elif attr_type == ValueTreeNode.NODE_ATTRIBUTE:
                child_value_tree_node = value_tree_node.getChild(name)
                self.visit(child_value_tree_node)

        self._onUp(value_tree_node, **kvargs)

    def _processValue(self, name: str, value_tree_value: ValueTreeValue) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _onDown(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _onUp(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _beforeDict(self, name: str, dict_: dict) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _afterDict(self, name: str, dict_: dict) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _beforeDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass

    def _afterDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        """Meant to be overridden by derived visitor objects"""
        pass


class AnytreeGenerator(ValueTreeVisitor):
    """Sets up a tree that can be used with the anytree library"""

    def __init__(
        self,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
        generator_options: Optional[GeneratorOptions] = None,
    ):
        super().__init__(tree_traversal_options)
        self._generator_options = generator_options or GeneratorOptions()
        self._stack: List[anytree.Node] = []
        self.root_node = None  # The root node of the generated tree

    def _generateAnytreeNode(self, name: Any) -> anytree.Node:
        """Generate an Anytree node and link it to the existing tree"""
        name_str = str(name)
        if self._generator_options.enforce_names_alpha:
            name_str = enforceNameStartsWithNameToken(name_str)

        if len(self._stack) > 0:
            parent_any_tree_node = self._stack[-1]
        else:
            parent_any_tree_node = None

        any_tree_node = anytree.Node(name_str, parent=parent_any_tree_node)

        if len(self._stack) == 0:
            self.root_node = any_tree_node

        return any_tree_node

    def _onDown(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        meta_tree_node = value_tree_node.getMetaTreeNode()
        name = kvargs.get("alias_name", meta_tree_node._name)
        any_tree_node = self._generateAnytreeNode(name)
        self._stack.append(any_tree_node)
        any_tree_node.value_tree_node = value_tree_node

    def _onUp(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        self._stack.pop()

    def _processValue(self, name: str, value_tree_value: ValueTreeValue) -> None:
        any_tree_node = self._generateAnytreeNode(name)
        any_tree_node.value_tree_value = value_tree_value

    def _beforeDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        any_tree_node = self._generateAnytreeNode(id_)
        self._stack.append(any_tree_node)

    def _afterDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        self._stack.pop()

    def _beforeDict(self, name: str, dict_: dict) -> None:
        any_tree_node = self._generateAnytreeNode(name)
        self._stack.append(any_tree_node)

    def _afterDict(self, name: str, dict_: dict) -> None:
        self._stack.pop()


# A nested directory as generated by the DictGenerator
TreeDict = Dict[str, Union[ValueType, Dict]]


class DictGenerator(ValueTreeVisitor):
    def __init__(
        self,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
        generator_options: Optional[GeneratorOptions] = None,
    ):
        super().__init__(tree_traversal_options)
        self.root_dict: TreeDict = {}  # The root dictionary
        self._stack: List[TreeDict] = [self.root_dict]
        self._generator_options = generator_options or GeneratorOptions()

    def _startChildDict(self) -> Tuple[TreeDict, TreeDict]:
        parent_dict: TreeDict = self._stack[-1]
        child_dict: TreeDict = {}
        self._stack.append(child_dict)
        return parent_dict, child_dict

    def _endChildDict(self) -> None:
        self._stack.pop()

    def _addDictEntry(self, parent_dict: TreeDict, name: Union[int, str], entry: Any):
        name_str: str
        if self._generator_options.enforce_names_alpha:
            name_str = enforceNameStartsWithNameToken(name)
        else:
            name_str = str(name)

        parent_dict[name_str] = entry

    def _processValue(self, name: str, value_tree_value: ValueTreeValue) -> None:
        parent_dict: TreeDict = self._stack[-1]
        self._addDictEntry(parent_dict, name, value_tree_value.getValue())

    def _onDown(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        meta_tree_node = value_tree_node.getMetaTreeNode()
        name = kvargs.get("alias_name", meta_tree_node._name)
        parent_dict, child_dict = self._startChildDict()
        self._addDictEntry(parent_dict, name, child_dict)

    def _onUp(self, value_tree_node: ValueTreeNode, **kvargs) -> None:
        self._endChildDict()

    def _beforeDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        parent_dict, child_dict = self._startChildDict()
        self._addDictEntry(parent_dict, id_, child_dict)

    def _afterDictEntry(self, id_: int, subtree: ValueTreeNode) -> None:
        self._endChildDict()

    def _beforeDict(self, name: str, dict_: dict) -> None:
        parent_dict, child_dict = self._startChildDict()
        self._addDictEntry(parent_dict, name, child_dict)

    def _afterDict(self, name: str, dict_: dict) -> None:
        self._endChildDict()


class LeafPathDumper(ValueTreeVisitor):
    """A visitor class that dumps the paths to all leaf nodes"""

    def __init__(
        self,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
        display_values=True,
        sink=print,
    ):
        super().__init__(tree_traversal_options)
        self.display_values = display_values
        self.sink = sink

    def _processValue(self, name: str, value_tree_value: ValueTreeValue) -> None:
        self.sink.output(
            "%s = '%s'" % (value_tree_value.getPath(), value_tree_value.getValue())
        )


class OutputSink(object):
    """A base class that enables flexible output generation"""

    def reset(self) -> None:
        pass

    def output(self, msg: str) -> None:
        pass

    def flush(self) -> str:
        pass


class PrintSink(OutputSink):
    """An output sink that prints directly to stdout via the print(...) function"""

    def output(self, msg: str) -> None:
        print(msg)


class StringSink(OutputSink):
    """An output sink that collects strings in a buffer"""

    def reset(self) -> None:
        self.buffer_: List[str] = []

    def output(self, msg: str) -> None:
        self.buffer_.append(msg)

    def flush(self) -> str:
        all_msg = "\n".join(self.buffer_)
        self.buffer_ = []
        return all_msg


class DocumentExplorer(object):
    def __init__(
        self,
        sink_type=PrintSink,
        display_values=True,
    ):
        self.sink = sink_type()
        self.display_values = display_values

    @staticmethod
    def generateAnytreeTree(
        document: ValueTreeNode,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
        generator_options: Optional[GeneratorOptions] = None,
    ) -> anytree.Node:
        """Generate an Anytree from a value tree"""
        tree_establisher = AnytreeGenerator(
            tree_traversal_options=tree_traversal_options,
            generator_options=generator_options,
        )
        tree_establisher.visit(document)

        return tree_establisher.root_node

    def dumpDocumentTree(
        self,
        document: ValueTreeNode,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
        generator_options: Optional[GeneratorOptions] = None,
    ) -> str:
        """Dump the document tree as a string"""

        generator_options = generator_options or GeneratorOptions()

        anytree_tree = DocumentExplorer.generateAnytreeTree(
            document=document,
            tree_traversal_options=tree_traversal_options,
            generator_options=generator_options,
        )

        self.sink.reset()

        # Non-ascii styles cause problems with encoding on Windows system
        if os.name == "nt":
            style = anytree.AsciiStyle()
        else:
            style = anytree.ContStyle()

        for pre, _, node in anytree.RenderTree(anytree_tree, style=style):

            if hasattr(node, "value_tree_value"):
                node_representation = prettyPrintValue(
                    node.value_tree_value,
                    display_values=self.display_values,
                    name_alias=node.name,
                )
            elif hasattr(node, "value_tree_node"):
                node_representation = prettyPrintNode(
                    node.value_tree_node,
                    display_values=self.display_values,
                    name_alias=node.name,
                )
            else:
                node_representation = node.name
            self.sink.output(f"{pre}{node_representation}")

        return self.sink.flush()

    def dumpDocumentLeafPaths(
        self,
        document: ValueTreeNode,
        tree_traversal_options: Optional[TreeTraversalOptions] = None,
    ) -> str:
        """Dump a list of paths to all leaf nodes"""
        self.sink.reset()
        tree_traversal_options = tree_traversal_options or TreeTraversalOptions(
            visit_dict_nodes=False
        )
        leaf_dumper = LeafPathDumper(
            tree_traversal_options=tree_traversal_options,
            display_values=self.display_values,
            sink=self.sink,
        )
        leaf_dumper.visit(document)
        return self.sink.flush()


def generateDictionary(
    document: ValueTreeNode,
    tree_traversal_options: Optional[TreeTraversalOptions] = None,
    generator_options: Optional[GeneratorOptions] = None,
) -> TreeDict:
    """Generate a tree of nested dicts from a value tree"""

    generator_options = generator_options or GeneratorOptions(enforce_names_alpha=True)

    dict_generator = DictGenerator(
        tree_traversal_options, generator_options=generator_options
    )
    dict_generator.visit(document)
    return dict_generator.root_dict


def dumpTreeTxt(
    value_tree_node: ValueTreeNode, display_values=True, only_base_tree=True
) -> str:
    """Dump a value tree as formatted text"""
    tree_traversal_options = TreeTraversalOptions(
        visit_dict_nodes=(only_base_tree is False)
    )

    document_explorer = DocumentExplorer(StringSink, display_values=display_values)
    document_tree_txt = document_explorer.dumpDocumentTree(
        value_tree_node, tree_traversal_options=tree_traversal_options
    )
    return document_tree_txt


def dumpDocumentStructureTxt(display_values=True, only_base_tree=True) -> str:
    """Dump the document structure of the main document as formatted text"""
    value_tree = generateDocumentTree()
    return dumpTreeTxt(
        value_tree, display_values=display_values, only_base_tree=only_base_tree
    )


def getSymbolTypeStructureTxt(
    display_values=True, only_base_tree=True
) -> Dict[str, str]:
    """Return a dict that maps symbol class strings to the formatted text of the corresponding symbol type"""
    document_trees_of_symbol_classes = getDocumentTreesOfDynamicTreeNodes()
    result: Dict[str, str] = {}
    for symbol_class, symbol_value_tree in document_trees_of_symbol_classes.items():
        result[symbol_class] = dumpTreeTxt(
            symbol_value_tree,
            display_values=display_values,
            only_base_tree=only_base_tree,
        )
    return result


def getDocumentStructureDocString(settings: Settings) -> str:
    """Return a representation of the main document and the symbol classes as formatted text"""
    display_values = False
    document_doc_string = dumpDocumentStructureTxt(display_values=display_values)
    symbol_doc_strings_by_type = getSymbolTypeStructureTxt(
        display_values=display_values
    )

    document_trees_of_symbol_classes_rendered = ""
    for symbol_class, symbol_representation in symbol_doc_strings_by_type.items():
        document_trees_of_symbol_classes_rendered += "<%s>\n%s\n\n" % (
            symbol_class,
            symbol_representation,
        )

    return """\
-------------------------------------------------------------------------------

elf_diff document structure:

%s

%s
-------------------------------------------------------------------------------

Tree entities are represented by nested classes in Python.

To print e.g. the binary path of the new binary do the following:

 print(document.files.input.new.binary_path)

Typed symbols are stored in dictionaries by their symbol id.
The following prints the code instructions associated with a newly appeared symbol.

 print(document.symbols.appeared[0].instructions)
""" % (
        document_doc_string,
        document_trees_of_symbol_classes_rendered,
    )
