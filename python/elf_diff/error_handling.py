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

from __future__ import print_function
import sys
import traceback


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def unrecoverableError(msg):

    eprint("Error: {msg}".format(msg=msg))

    traceback.print_stack()
    sys.exit(1)


def warning(msg):
    eprint("Warning: {msg}".format(msg=msg))
