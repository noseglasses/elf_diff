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

from elf_diff.error_handling import unrecoverableError
from elf_diff.error_handling import warning
from elf_diff.html import preHighlightSourceCode
from elf_diff.symbol import getSymbolType

import re


class Binary(object):
    def __init__(
        self,
        settings,
        filename,
        symbol_selection_regex=None,
        symbol_exclusion_regex=None,
    ):

        import os.path

        self.settings = settings
        self.filename = filename
        self.symbol_type = getSymbolType(settings.language)

        self.text_size = 0
        self.data_size = 0
        self.bss_size = 0
        self.overall_size = 0
        self.progmem_size = 0
        self.static_ram_size = 0

        self.symbol_selection_regex_compiled = None
        if symbol_selection_regex is not None:
            self.symbol_selection_regex_compiled = re.compile(symbol_selection_regex)

        self.symbol_exclusion_regex_compiled = None
        if symbol_exclusion_regex is not None:
            self.symbol_exclusion_regex_compiled = re.compile(symbol_exclusion_regex)

        if not self.filename:
            unrecoverableError("No binary filename defined")

        if not os.path.isfile(self.filename):
            unrecoverableError(
                "Unable to find filename {filename}".format(filename=filename)
            )

        self.symbols = {}

        self.parseSymbols()

    def readObjdumpOutput(self):

        import subprocess

        cmd = [self.settings.objdump_command, "-drwCS", self.filename]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        o, e = proc.communicate()

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def readNMOutput(self):

        import subprocess

        cmd = [
            self.settings.nm_command,
            "--print-size",
            "--size-sort",
            "--radix=d",
            "-C",
            self.filename,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        o, e = proc.communicate()

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def readSizeOutput(self):

        import subprocess

        cmd = [self.settings.size_command, self.filename]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        o, e = proc.communicate()

        output = o.decode("utf8")
        # error = e.decode('utf8')

        return output

    def addSymbol(self, symbol):
        symbol.init()

        self.symbols[symbol.name] = symbol

    def isSymbolSelected(self, symbol_name):
        if self.symbol_exclusion_regex_compiled is not None:
            if re.match(self.symbol_exclusion_regex_compiled, symbol_name):
                return False

        if self.symbol_selection_regex_compiled is None:
            return True

        if re.match(self.symbol_selection_regex_compiled, symbol_name):
            return True

        return False

    def determineSymbolSizes(self):

        size_output = self.readSizeOutput()

        size_re = re.compile(r"^\s*([0-9]+)\s+([0-9]+)\s+([0-9]+)\s+([0-9]+)")
        sizes_sucessfully_determined = False
        for line in size_output.splitlines():
            size_match = re.match(size_re, line)
            if size_match:
                self.text_size = int(size_match.group(1))
                self.data_size = int(size_match.group(2))
                self.bss_size = int(size_match.group(3))
                self.overall_size = int(size_match.group(4))

                self.progmem_size = self.text_size + self.data_size
                self.static_ram_size = self.data_size + self.bss_size

                sizes_sucessfully_determined = True

                break

        if not sizes_sucessfully_determined:
            warning(
                "Unable to determine resource consumptions. Is the proper size utility used?"
            )

    def getNextSymbol(self, symbol_name):
        if self.isSymbolSelected(symbol_name):
            # print("Considering symbol " + symbol_name)
            return self.symbol_type(symbol_name)
        # print("Ignoring symbol " + symbol_name)
        return None

    def gatherSymbolInstructions(self):
        objdump_output = self.readObjdumpOutput()

        # print("Output:")
        # print("%s" % (objdump_output))

        header_line_re = re.compile("^(0x)?[0-9A-Fa-f]+ <(.+)>:")
        instruction_line_re = re.compile(
            r"^\s*[0-9A-Fa-f]+:\s*((?:\s*[0-9a-fA-F]{2})+)\s+(.*)\s*"
        )

        cur_symbol = None
        n_symbols = 0
        n_instruction_lines = 0

        for line in objdump_output.splitlines():

            header_match = re.match(header_line_re, line)
            if header_match:
                if cur_symbol:
                    self.addSymbol(cur_symbol)
                    n_symbols += 1

                symbol_name = header_match.group(2)
                cur_symbol = self.getNextSymbol(symbol_name)
            else:
                instruction_line_match = re.match(instruction_line_re, line)
                if cur_symbol:
                    if instruction_line_match:
                        # print("Found instruction line \'%s\'" % (instruction_line_match.group(0)))
                        cur_symbol.addInstructions(instruction_line_match.group(2))
                        n_instruction_lines = n_instruction_lines + 1
                    else:
                        if (len(line) > 0) and (not line.isspace()):
                            cur_symbol.addInstructions(preHighlightSourceCode(line))

        if cur_symbol:
            self.addSymbol(cur_symbol)

        if n_instruction_lines == 0:
            warning(
                "Unable to read assembly from binary {filename}.".format(
                    filename=self.filename
                )
            )
            warning("Do you use the correct binutils version?")
            warning("Please check the --bin_dir and --bin_prefix settings.")

    def gatherSymbolProperties(self):
        nm_output = self.readNMOutput()

        self.num_symbols_dropped = 0
        nm_regex = re.compile(r"^[0-9A-Fa-f]+\s([0-9A-Fa-f]+)\s(\w)\s(.+)")
        for line in nm_output.splitlines():
            nm_match = re.match(nm_regex, line)

            if nm_match:
                symbol_size_str = nm_match.group(1)
                symbol_type = nm_match.group(2)
                symbol_name = nm_match.group(3)

                if symbol_name not in self.symbols.keys():
                    if self.isSymbolSelected(symbol_name):
                        data_symbol = self.symbol_type(symbol_name)
                        data_symbol.size = int(symbol_size_str)
                        data_symbol.type = symbol_type
                        self.addSymbol(data_symbol)
                    else:
                        self.num_symbols_dropped += 1
                else:
                    self.symbols[symbol_name].size = int(symbol_size_str)
                    self.symbols[symbol_name].type = symbol_type

    def parseSymbols(self):

        self.determineSymbolSizes()
        self.gatherSymbolInstructions()
        self.gatherSymbolProperties()

    def __eq__(self, other):

        if len(self.symbols) != len(other.symbols):
            # print("Number of symbols differs")
            return False

        # Check if symbol names differ

        old_symbols = set(self.symbols.keys())
        new_symbols = set(other.symbols.keys())

        only_in_self = old_symbols - new_symbols
        if len(only_in_self) > 0:
            # print("Some symbols only in self")
            return False

        only_in_other = new_symbols - old_symbols
        if len(only_in_other) > 0:
            # print("Some symbols only in other")
            return False

        # Check if actual symbols differ

        for symbol_name in self.symbols.keys():

            old_symbol = self.symbols[symbol_name]
            new_symbol = other.symbols[symbol_name]

            if not (old_symbol == new_symbol):
                return False

        # print("Symbols identical")

        return True

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)
