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
from elf_diff.meta_tree_properties import Properties
from elf_diff.tree_addressable import TreeAddressable
from elf_diff.tree_exception import TreeException

# Pylint rants about Dict being imported although used in type annotation comments
from typing import (  # pylint: disable=unused-import
    Optional,
    Callable,
    Tuple,
    Union,
    Dict,
    List,
    Any,
)  # pylint: disable=unused-import
import copy
import abc


class Node(TreeAddressable):
    """A common base class for all meta tree node types"""

    def __init__(self, name: str, *args):

        self._name: str = name

        self._properties: Optional[Properties] = None
        self._values = {}  # type: Dict[str, Value]
        self._children = {}  # type: Dict[str, Node]
        self._parent = None  # type: Optional[Node]

        self.parseOptionalArgs(*args)

    def parseOptionalArgs(self, *args: Any) -> None:
        """Parse any optional arguments"""
        for opt_arg in args:
            if isinstance(opt_arg, Properties):
                if self._properties is not None:
                    raise TreeException(self, "Properties ambiguously defined")
                self._properties = opt_arg
                self._properties.validate(self)

            elif issubclass(type(opt_arg), Node):
                node: Node = opt_arg
                self._children[node._name] = node
            elif isinstance(opt_arg, Value):
                value: Value = opt_arg
                self._values[value._name] = value
                value._parent = self
            elif isinstance(opt_arg, Multiple):
                multi_node: Multiple = opt_arg
                spawned = multi_node.spawn()
                # Pass the spawned nodes and values as if they would have been added
                # to this node's constructor
                self.parseOptionalArgs(*spawned)

    def getPath(self) -> str:
        """Return the formatted tree path of the node"""
        if self._parent is not None:
            return "%s.%s" % (self._parent.getPath(), self._name)
        if self._name is None:
            raise TreeException(self, "Encountered an unnamed node")
        return self._name

    def connectNodes(self) -> None:
        """Connect the tree nodes:
        Register parent with children and pass on properties.
        """
        if self._properties is None:
            self._properties = Properties()

        if self._parent is None:
            self._properties.configure(None)
        else:
            self._properties.configure(self._parent._properties)

        for child in self._children.values():
            child._parent = self
            # Recurse
            child.connectNodes()

        for value in self._values.values():
            value._parent = self
            value.configureProperties()

    def forEachChild(self, callable_: Callable) -> None:
        """Apply a callable to all children"""
        for key in sorted(self._children):
            child: Node = self._children[key]
            callable_(self, child)

    @abc.abstractmethod
    def configureValueTree(self, value_tree_node: Any, **kwargs: Any) -> None:
        pass


class Value(TreeAddressable):
    """A leaf node of the meta tree"""

    def __init__(self, name, *args):
        self._name = name
        self._properties = Properties(*args)
        self._parent: Node = None

    def getPath(self) -> str:
        return "%s.%s" % (self._parent.getPath(), self._name)

    def configureProperties(self) -> None:
        self._properties.configure(self._parent._properties)


class Multiple(object):
    """An auxiliary class that simplifies expressing node multiplicity
    in meta tree definitions
    """

    def __init__(self, names: Tuple[str], nested: Union[Node, Value]):
        self._names = names
        self._nested = nested

    def spawn(self) -> List[Union[Node, Value]]:
        """Spawn actual nodes"""
        spawned: List[Union[Node, Value]] = []
        for name in self._names:
            new_entity = copy.deepcopy(self._nested)
            new_entity._name = name
            spawned.append(new_entity)

        return spawned
