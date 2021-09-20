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


def tendencySymbol(from_size, to_size):
    if from_size > to_size:
        return "*"
    return ""


def formatMemChange(what, from_size, to_size):
    tendency_symbol = tendencySymbol(from_size, to_size)
    difference = to_size - from_size
    return "%s: %d -> %d bytes (%+d bytes) %s" % (
        what,
        from_size,
        to_size,
        difference,
        tendency_symbol,
    )


def listIntersection(l1, l2):
    return sorted(list(set(l1) & set(l2)))
