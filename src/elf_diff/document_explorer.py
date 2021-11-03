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
from elf_diff.pair_report_document import (
    ValueTreeNode,
    MetaTreeLeafNode,
    MetaDocument,
    getDocumentTreesOfSymbolClasses,
)
import anytree


class TreeTraversalOptions(object):
    """Options that affect how document trees or subtrees are traversed"""

    def __init__(self, visit_dict_nodes=False, visit_value_tree_nodes=False):
        self.visit_dict_nodes = visit_dict_nodes
        self.visit_value_tree_nodes = visit_value_tree_nodes


TREE_TRAVERSAL_ALL = TreeTraversalOptions(
    visit_dict_nodes=True, visit_value_tree_nodes=True
)


class MetaTreeNodeVisitor(object):
    def __init__(self, traversal_options=None):
        self.tree_traversal_options = traversal_options or TreeTraversalOptions()

    def traverseValueSubtree(self, node):
        if not isinstance(node._value, dict):
            return

        if self.tree_traversal_options.visit_dict_nodes:
            for key, value in node._value.items():
                self.beforeDictEntry(key, value)
                self.visit(value)
                self.afterDictEntry(key, value)

    def visit(self, node, **kvargs):
        # Some nodes store reference to nodes that are already stored in other
        # places of the tree. Those references are stored in the _value
        # member of the MetaTreeLeafNode.
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
        if isinstance(node, MetaTreeLeafNode):
            if isinstance(node._value, ValueTreeNode):
                if self.tree_traversal_options.visit_value_tree_nodes:
                    self.visit(node._value._m, alias_name=node._name)
                    return

        self.onDown(node, **kvargs)

        if isinstance(node, MetaTreeLeafNode):
            # MetaTreeLeafNode objects might store dict values that represent
            # subtrees (e.g. for storing the dynamically generated
            # collections of old/new/appeared/disappeared/... symbols in the
            # tree.
            self.traverseValueSubtree(node)
        else:
            node.forEachChild(lambda parent, child, visitor=self: visitor.visit(child))

        self.onUp(node, **kvargs)

    def onDown(self, meta_tree_node, **kvargs):
        """Meant to be overridden by derived visitor objects"""
        pass

    def onUp(self, meta_tree_node, **kvargs):
        """Meant to be overridden by derived visitor objects"""
        pass

    def beforeDictEntry(self, name, value):
        """Meant to be overridden by derived visitor objects"""
        pass

    def afterDictEntry(self, name, value):
        """Meant to be overridden by derived visitor objects"""
        pass


class AnytreeGeneratorOptions(object):
    def __init__(self, store_meta_tree_nodes=False, store_leaf_node_values=False):
        self.store_meta_tree_nodes = store_meta_tree_nodes
        self.store_leaf_node_values = store_leaf_node_values


class AnytreeGenerator(MetaTreeNodeVisitor):
    """Sets up a tree that can be used with the anytree library"""

    def __init__(self, tree_traversal_options=None, generator_options=None):
        super().__init__(tree_traversal_options)
        self.generator_options = generator_options or AnytreeGeneratorOptions()
        self.stack = []
        self.root_node = None  # The root node of the generated tree

    def onDown(self, meta_tree_node, **kvargs):
        if len(self.stack) > 0:
            parent_any_tree_node = self.stack[-1]
        else:
            parent_any_tree_node = None

        name = kvargs.get("alias_name", meta_tree_node._name)

        any_tree_node = anytree.Node(name, parent=parent_any_tree_node)

        if self.generator_options.store_meta_tree_nodes:
            any_tree_node.meta_tree_node = meta_tree_node

        if self.generator_options.store_leaf_node_values:
            if meta_tree_node.is_leaf:
                any_tree_node.value = meta_tree_node._value

        if len(self.stack) == 0:
            self.root_node = any_tree_node

        self.stack.append(any_tree_node)

    def onUp(self, meta_tree_node, **kvargs):
        self.stack.pop()


class DictGenerator(MetaTreeNodeVisitor):
    def __init__(self, tree_traversal_options=None):
        super().__init__(tree_traversal_options)
        self.root_dict = {}  # The root dictionary
        self.stack = [self.root_dict]

    def startChildDict(self):
        parent_dict = self.stack[-1]
        child_dict = {}
        self.stack.append(child_dict)
        return parent_dict, child_dict

    def endChildDict(self):
        self.stack.pop()

    def onDown(self, meta_tree_node, **kvargs):

        name = kvargs.get("alias_name", meta_tree_node._name)

        parent_dict, child_dict = self.startChildDict()

        if meta_tree_node.is_leaf:
            parent_dict[name] = meta_tree_node._value
        else:
            parent_dict[name] = child_dict

    def onUp(self, meta_tree_node, **kvargs):
        self.endChildDict()

    def beforeDictEntry(self, name, value):
        parent_dict, child_dict = self.startChildDict()
        parent_dict[name] = child_dict

    def afterDictEntry(self, name, value):
        self.endChildDict()


class LeafPathDumper(MetaTreeNodeVisitor):
    """A visitor class that dumps the paths to all leaf nodes"""

    def __init__(self, tree_traversal_options=None, display_values=True, sink=print):
        super().__init__(tree_traversal_options)
        self.display_values = display_values
        self.sink = sink

    def onDown(self, meta_tree_node, **kvargs):
        if meta_tree_node.is_leaf:
            self.sink.output(
                "%s = '%s'" % (meta_tree_node.getPath(), str(meta_tree_node._value))
            )


class OutputSink(object):
    """A base class that enables flexible output generation"""

    def init(self):
        pass

    def output(self, msg):
        pass

    def flush(self):
        pass


class PrintSink(OutputSink):
    """An output sink that prints directly to stdout via the print(...) function"""

    def output(self, msg):
        print(msg)


class StringSink(OutputSink):
    """An output sink that collects strings in a buffer"""

    def init(self):
        self.buffer_ = []

    def output(self, msg):
        self.buffer_.append(msg)

    def flush(self):
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
    def getMetaTreeNode(document):
        if isinstance(document, ValueTreeNode):
            return document._m
        return document

    @staticmethod
    def generateAnytreeTree(
        document, tree_traversal_options=None, generator_options=None
    ):
        meta_tree_node = DocumentExplorer.getMetaTreeNode(document)

        tree_establisher = AnytreeGenerator(
            tree_traversal_options=tree_traversal_options,
            generator_options=generator_options,
        )
        tree_establisher.visit(meta_tree_node)

        return tree_establisher.root_node

    def dumpDocumentTree(self, document, tree_traversal_options=None):
        anytree_tree = DocumentExplorer.generateAnytreeTree(
            document=document,
            tree_traversal_options=tree_traversal_options,
            generator_options=AnytreeGeneratorOptions(store_meta_tree_nodes=True),
        )

        self.sink.init()

        for pre, _, node in anytree.RenderTree(anytree_tree):
            self.sink.output(
                "%s%s"
                % (
                    pre,
                    node.meta_tree_node.prettyPrint(
                        self.display_values, name_alias=node.name
                    ),
                )
            )

        return self.sink.flush()

    def generateDictionary(self, document, tree_traversal_options=None):
        meta_tree_node = self.getMetaTreeNode(document)
        dict_generator = DictGenerator(tree_traversal_options)
        dict_generator.visit(meta_tree_node)
        return dict_generator.root_dict

    def dumpDocumentLeafPaths(self, document, tree_traversal_options=None):
        meta_tree_node = self.getMetaTreeNode(document)
        self.sink.init()
        leaf_dumper = LeafPathDumper(
            tree_traversal_options=tree_traversal_options,
            display_values=self.display_values,
            sink=self.sink,
        )
        leaf_dumper.visit(meta_tree_node)
        return self.sink.flush()


def getDocumentStructureDocString(settings):
    meta_document = MetaDocument()
    document_doc_string = DocumentExplorer(
        StringSink, display_values=False
    ).dumpDocumentTree(meta_document)

    document_trees_of_symbol_classes = getDocumentTreesOfSymbolClasses()

    document_trees_of_symbol_classes_rendered = ""
    for symbol_class, symbol_meta_tree in document_trees_of_symbol_classes.items():
        symbol_representation = DocumentExplorer(
            StringSink, display_values=False
        ).dumpDocumentTree(symbol_meta_tree)

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
