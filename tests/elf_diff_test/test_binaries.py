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
import os
import sys

TESTING_DIR: str = os.path.join(
    os.path.abspath(os.path.dirname(sys.modules[__name__].__file__)), ".."
)


def getTestBinary(platform: str, test_name: str, build_type: str, new_old: str) -> str:
    test_binary = os.path.join(
        TESTING_DIR,
        platform,
        "libelf_diff_%s_%s_%s.a" % (test_name, build_type, new_old),
    )
    assert os.path.exists(test_binary)
    return test_binary
