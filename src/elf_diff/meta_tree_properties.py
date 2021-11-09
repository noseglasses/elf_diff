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
from elf_diff.tree_exception import TreeException
from typing import Union, Callable, Dict, Any
from typing import Type as Type_
from typing import Set, Optional


class Property(object):
    pass


class Doc(Property):
    def __init__(self, doc: Optional[Union[str, Callable]]):
        self._doc = doc

    def format_(self, meta_tree_entity):
        # type: (Any) -> str
        """Evaluate based to a meta tree entity"""

        if self._doc is None:
            return ""

        if callable(self._doc):
            doc_callable: Callable = self._doc
            doc_string = doc_callable(meta_tree_entity)
        elif isinstance(self._doc, str):
            doc_string = self._doc
        else:
            raise TreeException(
                self, "Strange _doc property type. Must either be str or callable"
            )

        if doc_string is not None:
            formatted_doc_string = " [%s]" % doc_string
        else:
            formatted_doc_string = ""

        return formatted_doc_string


class Type(Property):
    def __init__(self, type_: Any):
        self._type = type_

    def validate(self, value):
        # type: (Any) -> None
        if not isinstance(value._value, self._type):
            raise TreeException(
                value,
                "Value type mismatch: Expected %s, obtained %s"
                % (str(self._type), str(type(value._value))),
            )


class AliasType(Property):
    def __init__(self, alias: Any):
        self._alias = alias


class Properties(object):
    TYPE_MAPPINGS: Dict[Type_[Property], str] = {
        Doc: "_doc",
        Type: "_type",
        AliasType: "_alias_type",
    }

    def __init__(self, *args):
        self._doc: Optional[Doc] = None
        self._type: Optional[Type_] = None
        self._alias_type: Optional[AliasType] = None

        self._args = args

    def validate(self, node):
        # type: (Any) -> None
        types_defined: Set[Type_] = set()
        for arg in self._args:
            # Pylint wants us to use isinstance, which is inappropriate here
            if type(arg) in types_defined:  # pylint: disable=unidiomatic-typecheck
                raise TreeException(
                    node, "Property type '%s' ambiguously defined" % type(arg)
                )
            types_defined.add(type(arg))

    def configure(self, parent_properties=None):
        # type: (Optional[Properties]) -> None

        if parent_properties is not None:
            for arg_name in Properties.TYPE_MAPPINGS.values():
                parent_prop = getattr(parent_properties, arg_name)
                setattr(self, arg_name, parent_prop)

        for arg in self._args:
            arg_name = Properties.TYPE_MAPPINGS[type(arg)]
            setattr(self, arg_name, arg)

        if self._doc is None:
            self._doc = Doc(None)
