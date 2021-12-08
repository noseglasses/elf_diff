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


class SourceFile(object):
    _CONSECUTIVE_ID = 0

    def __init__(self, path: str, path_wo_prefix: str):
        self.path: str = path
        self.path_wo_prefix: str = path_wo_prefix
        self.id_: int = SourceFile._getConsecutiveId()

    @staticmethod
    def _getConsecutiveId() -> int:
        """Return a consecutive unique id for assigning unique symbol ids"""
        tmp = SourceFile._CONSECUTIVE_ID
        SourceFile._CONSECUTIVE_ID += 1
        return tmp
