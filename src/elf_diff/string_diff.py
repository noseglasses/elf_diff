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
import difflib
from typing import List

HIGHLIGHT_START_TAG = "...HIGHLIGHT_START..."
HIGHLIGHT_END_TAG = "...HIGHLIGHT_END..."


def tagStringDiffSource(str1: str, str2: str):
    """Determine the difference between two strings, and tag them wrt. the source string"""
    seqm = difflib.SequenceMatcher(isjunk=None, a=str1, b=str2)
    output: List[str] = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():  # pylint: disable=unused-variable
        if opcode == "equal":
            output.append(str1[a0:a1])
        elif opcode == "insert":
            pass
        elif opcode == "delete":
            output.append(HIGHLIGHT_START_TAG + str1[a0:a1] + HIGHLIGHT_END_TAG)
        elif opcode == "replace":
            output.append(HIGHLIGHT_START_TAG + str1[a0:a1] + HIGHLIGHT_END_TAG)
        else:
            raise RuntimeError("unexpected opcode")

    return "".join(output)


def tagStringDiffTarget(str1: str, str2: str):
    """Determine the difference between two strings, and tag them wrt. the target string"""
    seqm = difflib.SequenceMatcher(isjunk=None, a=str1, b=str2)
    output = []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == "equal":
            output.append(str1[a0:a1])
        elif opcode == "insert":
            output.append(HIGHLIGHT_START_TAG + str2[b0:b1] + HIGHLIGHT_END_TAG)
        elif opcode == "delete":
            pass
        elif opcode == "replace":
            output.append(HIGHLIGHT_START_TAG + str2[b0:b1] + HIGHLIGHT_END_TAG)
        else:
            raise RuntimeError("unexpected opcode")

    return "".join(output)
