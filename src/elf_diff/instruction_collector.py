# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
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
from elf_diff.symbol import Symbol
from elf_diff.system_command import runSystemCommand
from elf_diff.binutils import Binutils
from elf_diff.error_handling import warning

from typing import Optional, Dict, List
import re
import progressbar  # type: ignore # Make mypy ignore this module
import sys

SOURCE_CODE_START_TAG = "...ED_SOURCE_START..."
SOURCE_CODE_END_TAG = "...ED_SOURCE_END..."


class InstructionCollector(object):
    def __init__(self, symbols):
        # type: (Dict[str, Symbol]) -> None

        self.symbols: Dict[str, Symbol] = symbols

        self.header_line_re = re.compile("^(0x)?[0-9A-Fa-f]+ <(.+)>:")
        self.instruction_line_re = re.compile(
            r"^\s*[0-9A-Fa-f]+:\s*((?:\s*[0-9a-fA-F]{2})+)\s+(.*)\s*"
        )
        self.cur_symbol: Optional[Symbol] = None
        self.n_instruction_lines: int = 0

        self._buffered_lines: List[str] = []

    def _cleanBufferedLines(self) -> None:
        if len(self._buffered_lines) == 0:
            return

        # Find the first empty line before the first non-empty line before
        # the first instruction line. We only want to have the first
        # non-empty block of context source code considered.
        first_index = len(self._buffered_lines)
        for i, e in reversed(list(enumerate(self._buffered_lines))):
            if e == "":
                break
            first_index = i

        self._buffered_lines = self._buffered_lines[first_index:]

    def _flushBufferedLines(self) -> None:
        if self.cur_symbol:
            for line in self._buffered_lines:
                self.cur_symbol.addInstructions(line)
        self._buffered_lines = []

    def _bufferLine(self, line: str) -> None:
        self._buffered_lines.append(line)

    def _submitSymbol(self) -> None:
        """Submit the most recent symbol that was collected"""
        if self.cur_symbol is not None:
            self._flushBufferedLines()
            self.cur_symbol = None

    def _checkSymbolHeaderLine(self, line: str) -> bool:
        """Check a line read from a file and process it if it is a symbol header line"""
        header_match = re.match(self.header_line_re, line)
        if header_match:
            if self.cur_symbol:
                self._submitSymbol()

            symbol_name_mangled: str = header_match.group(2)

            if symbol_name_mangled in self.symbols.keys():
                self.cur_symbol = self.symbols[symbol_name_mangled]
            return True

        return False

    @staticmethod
    def _unifyX86InstructionLine(line: str) -> str:
        # The x86 instruction 0xC3 is named retq for 64 bit and ret for 32 bit.
        # Strangely several versions of objdump, namely 2.34 and 2.36.1 output either 'ret' or 'retq'
        # both for x86_64 binaries.
        #
        # To make comparing files portable, replace the retq with ret.
        return re.sub(r"(^.*\sc3\s+)retq(.*)$", r"\1ret\2", line)

    def _unifyInstructionLine(self, line: str) -> str:
        """Fixup the assembly output by objdump in a way that it
        is the same for all versions of objdump
        """
        if self.file_format and (self.file_format == "elf64-x86-64"):
            return InstructionCollector._unifyX86InstructionLine(line)
        return line

    def registerSourceLine(self, line: str) -> None:
        if line.startswith(SOURCE_CODE_START_TAG):
            if line == SOURCE_CODE_START_TAG:
                # Empty line
                self._bufferLine("")
            else:
                source_code_line = "%s%s" % (line, SOURCE_CODE_END_TAG)
                self._bufferLine(source_code_line)

    def gatherSymbolInstructions(
        self, filename: str, file_format: Optional[str], binutils: Binutils
    ) -> None:
        """Gather the symbol instructions of a symbol"""
        if binutils.objdump_command is None:
            warning(
                "Binutils objdump command unavailable. Unable to collect instructions."
            )
            return

        self.file_format = file_format

        print("Gathering instructions")
        sys.stdout.flush()

        objdump_output: str = runSystemCommand(
            [
                binutils.objdump_command,
                "-drwS",
                "--source-comment=%s" % SOURCE_CODE_START_TAG,
                filename,
            ]
        )

        in_instruction_lines: bool = False
        for line in progressbar.progressbar(objdump_output.splitlines()):
            unified_line = self._unifyInstructionLine(line)

            is_header_line: bool = self._checkSymbolHeaderLine(unified_line)
            if is_header_line:
                in_instruction_lines = False
                continue

            instruction_line_match = re.match(self.instruction_line_re, unified_line)

            if instruction_line_match:
                if not in_instruction_lines:
                    # Clean the source lines buffered so far
                    self._cleanBufferedLines()
                    in_instruction_lines = True
                self.n_instruction_lines += 1

            if self.cur_symbol:
                if instruction_line_match:
                    instruction_line = instruction_line_match.group(2)
                    self._bufferLine(instruction_line)
                    # print("Found instruction line \'%s\'" % (unified_instruction_line))
                else:
                    self.registerSourceLine(unified_line)

        if self.cur_symbol:
            self._submitSymbol()
