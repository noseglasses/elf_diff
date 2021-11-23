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
from elf_diff.binutils import Binutils
from elf_diff.error_handling import warning

import re
from typing import Optional


def determineBinaryFileFormat(filename: str, binutils: Binutils) -> Optional[str]:
    """Get information about the architecture of the binary"""
    if binutils.objdump_command is None:
        warning(
            "Binutils objdump command unavailable. Unable to determine binary file format."
        )
        return None

    objdump_output: str = runSystemCommand([binutils.objdump_command, "-a", filename])
    file_format_match = re.search(r"file format\s+(\S+)", objdump_output)
    file_format: Optional[str] = None
    if file_format_match:
        file_format = file_format_match.group(1)
        print("File format of binary %s: %s" % (filename, file_format))
    else:
        print("Unable to detect binary file format of %s" % filename)

    return file_format
