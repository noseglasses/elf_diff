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
from typing import List, Dict, Optional, Any, Type, Tuple


class Symbol(object):

    TYPE_FUNCTION = 1
    TYPE_DATA = 2

    _CONSECUTIVE_ID = 0

    def __init__(self, name, name_mangled, is_demangled):
        """Initialize symbol object."""
        self.name: str = name
        self.name_mangled: str = name_mangled
        self.is_demangled: bool = is_demangled
        self.instruction_lines: List[str] = []
        self.size: int = 0
        self.type_: str = "?"
        self.source_id: Optional[int] = None
        self.source_line: Optional[int] = None
        self.id_: int

    @staticmethod
    def _getConsecutiveId() -> int:
        """Return a consecutive unique id for assigning unique symbol ids"""
        tmp = Symbol._CONSECUTIVE_ID
        Symbol._CONSECUTIVE_ID += 1
        return tmp

    def init(self) -> None:
        """A delayed initialization method"""
        self.instructions: str = ""
        instructions_for_hash: str = ""
        for instruction_line in self.instruction_lines:
            self.instructions += "%s\n" % instruction_line
            instructions_for_hash += "".join(instruction_line)
        self.instructions_hash = hash(instructions_for_hash)
        self.id_ = Symbol._getConsecutiveId()

    def hasInstructions(self) -> bool:
        """Check wether a symbol has related assmbly instructions"""
        return len(self.instruction_lines) > 0

    def addInstructions(self, instruction_line: str) -> None:
        """Add a line of assmbly instructions"""
        instruction_line_stripped = instruction_line.strip()
        self.instruction_lines.append(instruction_line_stripped)

    def instructionsEqual(self, other):
        # type: (Symbol) -> bool
        """Check if the instructions of two symbols equal"""
        if not len(self.instruction_lines) == len(other.instruction_lines):
            # print("Instructions differ")
            return False

        symbol_diff: List[str] = [
            i for i, j in zip(self.instruction_lines, other.instruction_lines) if i != j
        ]
        if len(symbol_diff) > 0:
            # print("Symbols differ")
            return False

        return True

    def __eq__(self, other):
        # type: (object) -> bool
        """Compare two symbols."""
        if not isinstance(other, Symbol):
            raise Exception("Trying to compare Symbol with %s" % type(other).__name__)

        if not self.name_mangled == other.name_mangled:
            # print("Symbol name differs")
            return False

        if not self.size == other.size:
            return False

        if not self.instructionsEqual(other):
            return False

        # print("Symbols equal")
        return True

    def livesInProgramMemory(self) -> bool:
        """Return True if the symbol is of a type that is stored in program memory (on a Harvard system)"""
        return (
            (self.type_ != "B")
            and (self.type_ != "b")
            and (self.type_ != "S")
            and (self.type_ != "s")
        )


class CppSymbol(Symbol):

    # Keep the order in this list sorted from most common property to
    # least common.
    PROPS: List[str] = ["full_name", "arguments", "namespace", "template_parameters"]

    SYMBOL_PREFIX: Dict[str, int] = {"non-virtual thunk to": 1, "vtable for": 2}

    def __init__(self, name: str, name_mangled: str, is_demangled: bool):
        """Initialize cpp symbol object."""
        super(CppSymbol, self).__init__(name, name_mangled, is_demangled)

        self.initProps()
        self.name_hash: int = hash(name_mangled)
        self.prefix_id: Optional[int] = None

    def initProps(self):
        for prop in self.PROPS:
            setattr(self, prop, None)

    @staticmethod
    def _getArgumentsPortion(
        input_str: str, opening_brace: str, closing_brace: str
    ) -> Tuple[Optional[str], Optional[str]]:
        closing_bracket_found: bool = False
        n: int = 0
        lower_brace_pos: Optional[int] = None
        upper_brace_pos: Optional[int] = None
        for i in reversed(range(len(input_str))):
            if (not closing_bracket_found) and (input_str[i] == closing_brace):
                closing_bracket_found = True
                upper_brace_pos = i
                n = 1
                continue
            if input_str[i] == opening_brace:
                n -= 1
                if n == 0:
                    lower_brace_pos = i
                    break
            elif input_str[i] == closing_brace:
                n += 1

        if lower_brace_pos is not None:
            arguments: str = input_str[lower_brace_pos + 1 : upper_brace_pos]
            rest: str = input_str[:lower_brace_pos]
            # print(f"{input_str} -> rest = {rest}, arguments = {arguments}")
            return rest, arguments

        return None, None

    def parseSignature(self) -> None:
        """Parse the symbol signature"""
        rest: Optional[str] = self.name

        # Consider special prefix
        for prefix, prefix_id in self.SYMBOL_PREFIX.items():
            if self.name.startswith(prefix):
                rest = self.name[len(prefix) + 1 :]  # Ignore the space after the prefix
                self.prefix_id = prefix_id
                break

        self.arguments: Optional[str]
        if rest is not None:
            rest, self.arguments = CppSymbol._getArgumentsPortion(rest, "(", ")")

        self.symbol_type: int
        if rest is not None:
            self.symbol_type = Symbol.TYPE_FUNCTION
        else:
            rest = self.name
            self.symbol_type = Symbol.TYPE_DATA

        # Check if the symbol lives within a class or namespace.
        # We cannot distinguish between those two as from a naming perspective both are equal.
        namespace_sep_pos: int = rest.rfind("::")
        self.full_name: str
        self.namespace: Optional[str]
        if namespace_sep_pos >= 0:
            self.full_name = rest[namespace_sep_pos + 2 :]
            full_namespace: Optional[str] = rest[:namespace_sep_pos]

            if full_namespace is not None:
                (
                    self.namespace,
                    self.template_parameters,
                ) = CppSymbol._getArgumentsPortion(full_namespace, "<", ">")
                if self.namespace is None:
                    self.namespace = full_namespace
        else:
            self.full_name = rest

        for prop in self.PROPS:
            prop_value: Any = getattr(self, prop)
            if prop_value is not None:
                setattr(self, prop + "_hash", hash(prop_value))

    def init(self) -> None:
        """Enables delayed initialization"""
        self.parseSignature()
        super().init()

    def propertiesEqual(self, other):
        # type: (CppSymbol) -> bool
        """Check whether the properties of two symbols equal"""
        for prop in self.PROPS:
            self_attr: Any = getattr(self, prop)
            other_attr: Any = getattr(other, prop)
            if self_attr != other_attr:
                return False

        return True

    def getProperties(self) -> Dict[str, Any]:
        """Get all properties of the symbol"""
        self_props: Dict[str, Any] = {}
        for prop in self.PROPS:
            self_props[prop] = getattr(self, prop)
        return self_props


def getSymbolType(language: str) -> Type[Symbol]:
    """Get an appropriate symbol type for a given language the binaries were compiled from"""
    if language == "c++":
        return CppSymbol

    raise Exception(f"Unknown language definition '{language}' encountered")
