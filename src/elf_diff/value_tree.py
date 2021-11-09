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
from elf_diff.meta_tree import Value as MetaTreeValue

# MetaTreeNode used for type checking. Pylint seems not to see that.
from elf_diff.meta_tree import Node as MetaTreeNode  # pylint: disable=unused-import
from elf_diff.tree_exception import TreeException

# Type Any used for type checking. Pylint seems not to see that.
from typing import (  # pylint: disable=unused-import
    Union,
    Dict,
    Type,
    Any,  # pylint: disable=unused-import
)

ValueType = Union[str, int, float, dict]


class Value(object):
    def __init__(self, value: ValueType, meta_tree_value: MetaTreeValue):
        self._value = value
        self._meta_tree_value = meta_tree_value

    def getDocumentation(self) -> str:
        """Get a formatted version of the documentation"""
        if self._meta_tree_value._properties._doc is None:
            raise TreeException(self._meta_tree_value, "Missing documentation")
        return self._meta_tree_value._properties._doc.format_(self._meta_tree_value)

    def getName(self) -> str:
        return self._meta_tree_value._name

    def getType(self) -> Type:
        return type(self._value)

    def getValue(self) -> ValueType:
        return self._value

    def getFormattedTypeInfo(self) -> str:
        if self._meta_tree_value._properties._alias_type is not None:
            return (
                " <%s>" % self._meta_tree_value._properties._alias_type._alias.__name__
            )
        elif self._meta_tree_value._properties._type is not None:
            return " <%s>" % self._meta_tree_value._properties._type._type.__name__

        return ""

    def getPath(self):
        return self._meta_tree_value.getPath()

    def validate(self) -> None:
        """Validate the leaf node"""
        if self._meta_tree_value._properties._type is not None:
            self._meta_tree_value._properties._type.validate(self)


class Node(object):
    """A node of the tree that represents the document externally"""

    NODE_ATTRIBUTE = 1
    VALUE_ATTRIBUTE = 2

    def __init__(self):
        self.attachMetaTreeNode(None)

    def __getattr__(self, name):
        # type: (str) -> Any
        """An overloaded attribute getter method that helps with error reporting
        when developing Jinja templates.

        name: The name of the member to be accessed.
        """
        if name not in self.__dict__.keys():
            # print("Members available")
            # for key in self.__dict__.keys():
            #    print("   %s" % key)
            raise Exception(
                "Tree node %s does not have a member '%s'" % (self.getPath(), name)
            )
        return self.__dict__[name]

    def __setattr__(self, name: str, value: ValueType) -> None:
        """An overloaded attribute setter method that takes care of notifying the associated
        meta tree node of the value update.
        """
        super().__setattr__(name, value)

        meta_tree_node = self.getMetaTreeNode()
        if name not in meta_tree_node._values.keys():
            raise TreeException(
                meta_tree_node, f"Trying to assign to undefined member '{name}'"
            )

        if value is not None:
            self.getValue(name).validate()

    def attachMetaTreeNode(self, meta_tree_node):
        # type: (MetaTreeNode) -> None
        """Attach the associated meta tree node"""
        self.__dict__[
            "_m"
        ] = meta_tree_node  # Not using setattr(...) prevents __setattr__ being invoked

    def addChild(self, name, value_tree_node):
        # type: (str, Node) -> None
        """Add a child value tree node"""
        self.__dict__[name] = value_tree_node

    def getMetaTreeNode(self):
        # type: () -> MetaTreeNode # Class Node yet undeclared at this point
        """Return the associated meta tree node"""
        return self.__dict__["_m"]

    def getPath(self) -> str:
        """Return a formatted version of the node's tree path"""
        meta_tree_node = self.getMetaTreeNode()
        return meta_tree_node.getPath()

    def getValue(self, name) -> Value:
        return Value(getattr(self, name), self.getMetaTreeNode()._values[name])

    def getValues(self) -> Dict[str, Value]:
        meta_tree_values = self.getMetaTreeNode()._values
        values: Dict[str, Value] = {}
        for name, meta_tree_value in meta_tree_values.items():
            values[meta_tree_value._name] = self.getValue(name)
        return values

    def getChild(self, name):
        # type: (str) -> Node
        return getattr(self, name)

    def getChildren(self):
        # type: () -> Dict[str, Node]
        children: Dict[str, Node] = {}
        meta_tree_children = self.getMetaTreeNode()._children
        for name, meta_tree_child in meta_tree_children.items():
            children[meta_tree_child._name] = self.getChild(name)
        return children

    def getDocumentation(self) -> str:
        """Get a formatted version of the documentation"""
        meta_tree_node = self.getMetaTreeNode()
        if meta_tree_node._properties is None:
            raise TreeException(meta_tree_node, "Missing properties")
        if meta_tree_node._properties._doc is None:
            raise TreeException(meta_tree_node, "Missing documentation")

        return meta_tree_node._properties._doc.format_(self)

    def getName(self) -> str:
        """Return the node's name"""
        return self.getMetaTreeNode()._name

    def getValueAndChildAttributes(self) -> Dict[str, int]:
        attrs: Dict[str, int] = {}

        children = self.getChildren()
        for name in children.keys():
            attrs[name] = Node.NODE_ATTRIBUTE

        values = self.getValues()
        for name in values.keys():
            attrs[name] = Node.VALUE_ATTRIBUTE

        return attrs
