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
from elf_diff.system_command import runSystemCommand
from elf_diff.source_file import SourceFile
from elf_diff.symbol import Symbol
from elf_diff.binutils import Binutils
from elf_diff.error_handling import warning

from typing import Dict, Optional
import re


class DebugInformationCollector(object):
    def __init__(self, symbols: Dict[str, Symbol], source_prefix: Optional[str]):
        self._symbols: Dict[str, Symbol] = symbols
        self._source_prefix: Optional[str] = source_prefix

        self._header_line_regex = re.compile(
            r"\s*<[0-9a-f]+>\s*<[0-9a-f]+>:\s+Abbrev Number:\s*(\d+)\s+\((\w+)\).*"
        )
        self._info_line_regex = re.compile(r"\s*<[0-9a-f]+>\s+(\S+)\s*:\s*(\S.*)")
        self._name_regex = re.compile(r".*\s+(\S+)")
        self._source_file_regex = re.compile(r".*\s+(\S+)")
        self._producer_regex = re.compile(r"\s*\([^\)]+\):\s+(.+)")

        self._header_id: Optional[int] = None
        self._header_tag: Optional[str] = None

        self._name: Optional[str] = None
        self._name_mangled: Optional[str] = None
        self._source_id: Optional[int] = None
        self._source_line: Optional[int] = None
        self._source_column: Optional[int] = None

        self._source_path_complete: Optional[str] = None
        self._producer: Optional[str] = None

        self._source_file_mapping: Dict[
            int, SourceFile
        ] = {}  # Maps a dwarf source id to an elf_diff SourceFile

        self.debug_info_available = False
        self.source_files: Dict[int, SourceFile] = {}

    def _registerSourceFile(
        self, source_path_base: str, source_path_complete: str, producer: str
    ) -> SourceFile:
        new_source_file = SourceFile(
            path_base=source_path_base,
            path_complete=source_path_complete,
            producer=producer,
        )
        self.source_files[new_source_file.id_] = new_source_file
        return new_source_file

    def _flushDataSet(self) -> None:
        lookup_name: Optional[str] = None
        if self._name_mangled is not None:
            lookup_name = self._name_mangled
        elif self._name is not None:
            lookup_name = self._name

        if lookup_name:
            if lookup_name in self._symbols.keys():
                symbol = self._symbols[lookup_name]

                assert self._source_id is not None
                symbol.source_id = self._source_id
                symbol.source_line = self._source_line
                symbol.source_column = self._source_column

        if self._source_path_complete is not None:
            if self._producer is None:
                raise Exception("Missing Dwarf producer info in elf file")
            if self._header_id is None:
                raise Exception("Missing Dwarf source file id in elf file")

            source_path_base = self._removeSourcePrefix(self._source_path_complete)
            source_file = self._registerSourceFile(
                source_path_base=source_path_base,
                source_path_complete=self._source_path_complete,
                producer=self._producer,
            )

            dwarf_source_id = self._header_id
            self._source_file_mapping[dwarf_source_id] = source_file

        self._name = None
        self._name_mangled = None
        self._source_line = None
        self._source_column = None

        self._source_path_complete = None
        self._producer = None

    def _removeSourcePrefix(self, filename: str) -> str:
        if self._source_prefix is None:
            return filename

        if filename.startswith(self._source_prefix):
            return filename[len(self._source_prefix) :]
        return filename

    def _processHeaderLine(self, line: str) -> bool:
        header_line_match = re.match(self._header_line_regex, line)
        if header_line_match:
            self._flushDataSet()
            self._header_id = int(header_line_match.group(1))
            self._header_tag = header_line_match.group(2)
            return True
        return False

    def _processNameAttribute(self, add_info: str) -> None:
        if self._header_tag == "DW_TAG_compile_unit":
            source_file_match = re.match(self._source_file_regex, add_info)
            if source_file_match is None:
                raise Exception("Unable to determine source filename from dwarf output")
            self._source_path_complete = source_file_match.group(1)
        else:
            self._name = add_info

    def _processProducerAttribute(self, add_info: str) -> None:
        if self._header_tag == "DW_TAG_compile_unit":
            producer_match = re.match(self._producer_regex, add_info)
            if producer_match is None:
                raise Exception(
                    "Unable to determine source file producer from dwarf output"
                )
            self._producer = producer_match.group(1)

    def _processInfoLine(self, line: str) -> None:
        info_line_match = re.match(self._info_line_regex, line)
        if info_line_match is None:
            return

        tag: str = info_line_match.group(1)
        add_info: str = info_line_match.group(2)

        if tag == "DW_AT_linkage_name":
            name_match = re.match(self._name_regex, add_info)
            if name_match is None:
                raise Exception("Undeciferable info line '%s'" % line)
            self._name_mangled = name_match.group(1)
        elif tag == "DW_AT_decl_file":
            dwarf_source_id = int(add_info)
            self._source_id = self._source_file_mapping[dwarf_source_id].id_
        elif tag == "DW_AT_decl_line":
            self._source_line = int(add_info)
        elif tag == "DW_AT_decl_column":
            self._source_column = int(add_info)
        elif tag == "DW_AT_name":
            self._processNameAttribute(add_info)
        elif tag == "DW_AT_producer":
            self._processProducerAttribute(add_info)

    def gatherDebugInformation(self, filename: str, binutils: Binutils) -> None:
        if binutils.readelf_command is None:
            warning(
                "Binutils readelf command unavailable. Unable to gather debug information."
            )
            return

        readelf_output = runSystemCommand(
            [
                binutils.readelf_command,
                "--debug-dump=info",
                filename,
            ]
        )

        self.debug_info_available = (
            r"Contents of the .debug_info section:" in readelf_output
        )

        if not self.debug_info_available:
            return

        for line in readelf_output.splitlines():
            if self._processHeaderLine(line):
                continue

            self._processInfoLine(line)

        # There might be a last ungoing data set being parsed
        self._flushDataSet()
