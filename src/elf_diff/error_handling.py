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

import sys

WARNINGS_OCCURRED = False


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class UnrecoverableError(Exception):
    pass


def unrecoverableError(msg):
    raise UnrecoverableError("{msg}".format(msg=msg))


def warning(msg):
    warning_unicode = "\u26A0"
    warning_cascade = warning_unicode * 3
    eprint(f"{warning_cascade} Warning: {msg} {warning_cascade}")
    global WARNINGS_OCCURRED
    WARNINGS_OCCURRED = True
