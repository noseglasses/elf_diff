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
import inspect
import os
from distutils import dir_util


def listIntersection(l1, l2):
    return sorted(list(set(l1) & set(l2)))


def getDirectoryThatStoresModule(obj):
    file_that_stores_class = inspect.getfile(type(obj))
    return os.path.dirname(file_that_stores_class)


def deprecationWarning(feature):
    print(
        """\
*******************************************************************************
PLEASE NOTE: Feature '%s' is deprecated and will likely be removed
             from future versions of the software.
*******************************************************************************
"""
        % feature
    )


def getRelpath(html_output_file, target_dir):
    html_dirname = os.path.dirname(html_output_file)
    return os.path.relpath(target_dir, html_dirname)


def recursiveCopy(source_dir, target_dir):
    dir_util.copy_tree(source_dir, target_dir)
