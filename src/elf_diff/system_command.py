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
from typing import List
import subprocess  # nosec # silence bandid warning


def runSystemCommand(cmd: List[str]) -> str:
    """Read the output of the objdump command applied to the binary"""
    proc = subprocess.Popen(  # nosec # silence bandid warning
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    o, e = proc.communicate()  # pylint: disable=unused-variable

    output: str = o.decode("utf8")
    # error = e.decode('utf8')

    return output
