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

from elf_diff.html import postHighlightSourceCodeRemoveTags
from elf_diff.html import postHighlightSourceCode
from elf_diff.html import escapeString

import difflib


class Symbol(object):

    type_function = 1
    type_data = 2
    consecutive_id = 0

    def __init__(self, name):
        self.name = name
        self.instruction_lines = []
        self.size = 0
        self.type = "?"
        self.id = Symbol.getConsecutiveId()

    def getConsecutiveId():
        tmp = Symbol.consecutive_id
        Symbol.consecutive_id += 1
        return tmp

    def init(self):
        self.instructions = ""
        for instruction_line in self.instruction_lines:
            self.instructions += "".join(instruction_line.split())
        self.instructions_hash = hash(self.instructions)

    def addInstructions(self, instruction_line):
        self.instruction_lines.append(instruction_line)

    def instructionsEqual(self, other):
        if not len(self.instruction_lines) == len(other.instruction_lines):
            # print("Instructions differ")
            return False

        symbol_diff = [
            i for i, j in zip(self.instruction_lines, other.instruction_lines) if i != j
        ]
        if len(symbol_diff) > 0:
            # print("Symbols differ")
            return False

        return True

    def __eq__(self, other):
        if not self.name == other.name:
            # print("Symbol name differs")
            return False

        if not self.size == other.size:
            return False

        if not self.instructionsEqual(other):
            return False

        # print("Symbols equal")
        return True

    def getDifferencesAsString(self, other, indent):
        diff = difflib.ndiff(self.instruction_lines, other.instruction_lines)
        # print list(diff)
        return postHighlightSourceCodeRemoveTags(
            indent + ("\n" + indent).join(list(diff))
        )

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

    def getInstructionsBlockEscaped(self, indent):
        if self.symbol_type == Symbol.type_data:
            return "<data symbol -> no assembly displayed>"
        return postHighlightSourceCode(
            escapeString(indent + ("\n" + indent).join(self.instruction_lines))
        )

    def livesInProgramMemory(self):
        return (
            (self.type != "B")
            and (self.type != "b")
            and (self.type != "S")
            and (self.type != "s")
        )


class CppSymbol(Symbol):

    # Keep the order in this list sorted from most common property to
    # least common.
    props = ["full_name", "arguments", "namespace", "template_parameters"]

    symbol_prefix = {"non-virtual thunk to": 1, "vtable for": 2}

    def __init__(self, name):
        super(CppSymbol, self).__init__(name)

        self.initProps()
        self.name = name
        self.name_hash = hash(name)
        self.prefix_id = None

    def initProps(self):
        for prop in self.props:
            setattr(self, prop, None)

    def __getArgumentsPortion(self, input_str, opening_brace, closing_brace):
        closing_bracket_found = False
        n = 0
        lower_brace_pos = None
        upper_brace_pos = None
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
            arguments = input_str[lower_brace_pos + 1 : upper_brace_pos]
            rest = input_str[:lower_brace_pos]
            # print(f"{input_str} -> rest = {rest}, arguments = {arguments}")
            return rest, arguments

        return None, None

    def __parseSignature(self):

        rest = self.name

        # Consider special prefix
        for prefix, prefix_id in self.symbol_prefix.items():
            if rest.startswith(prefix):
                rest = rest[len(prefix) + 1 :]  # Ignore the space after the prefix
                self.prefix_id = prefix_id

        rest, self.arguments = self.__getArgumentsPortion(rest, "(", ")")
        if rest is not None:
            self.symbol_type = Symbol.type_function
        else:
            rest = self.name
            self.symbol_type = Symbol.type_data

        # Check if the symbol lives within a class or namespace.
        # We cannot distinguish between those two as from a naming perspective both are equal.
        namespace_sep_pos = rest.rfind("::")
        if namespace_sep_pos >= 0:
            self.full_name = rest[namespace_sep_pos + 2 :]
            full_namespace = rest[:namespace_sep_pos]

            self.namespace, self.template_parameters = self.__getArgumentsPortion(
                full_namespace, "<", ">"
            )
            if self.namespace is None:
                self.namespace = full_namespace
        else:
            self.full_name = rest

        for prop in self.props:
            prop_value = getattr(self, prop)
            if prop_value is not None:
                setattr(self, prop + "_hash", hash(prop_value))

    def init(self):
        self.__parseSignature()
        super(CppSymbol, self).init()

    def propertiesEqual(self, other):
        for prop in self.props:
            self_arg = getattr(self, prop)
            other_arg = getattr(other, prop)
            if self_arg != other_arg:
                return False

        return True

    def getProperties(self):
        self_props = {}
        for prop in self.props:
            self_props[prop] = getattr(self, prop)
        return self_props


def getSymbolType(language):
    if language == "c++":
        return CppSymbol

    return None
