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
import inspect
import os
import re
from distutils import dir_util
from typing import List, Set


def setIntersection(l1: Set, l2: Set) -> List:
    """Return a list that is a sorted set intersection of two sets"""
    return sorted(list(set(l1) & set(l2)))


def getDirectoryThatStoresModuleOfObj(obj: object) -> str:
    """Return the directory that is the base path of a Python module that defines a given object"""
    file_that_stores_class = inspect.getfile(type(obj))
    return os.path.dirname(file_that_stores_class)


def getDirectoryThatStoresModule(module) -> str:
    """Return the base directory of a module"""
    return os.path.dirname(module.__file__)


def deprecationWarning(feature: str) -> None:
    """Print a deprecation warning for a given feature"""
    print(
        """\
*******************************************************************************
PLEASE NOTE: Feature '%s' is deprecated and will likely be removed
             from future versions of the software.
*******************************************************************************
"""
        % feature
    )


def getRelpath(html_output_file: str, target_dir: str) -> str:
    """Get the relative path of the storage location of a file with respect to a target directory"""
    html_dirname = os.path.dirname(html_output_file)
    return os.path.relpath(target_dir, html_dirname)


def recursiveCopy(source_dir: str, target_dir: str) -> None:
    """Copy the content of a source directory recursively (including subdirectories) to a target directory"""
    dir_util.copy_tree(source_dir, target_dir)


def isNameToken(str_: str) -> bool:
    """Check it a token is a name token in a programming language sense"""
    return re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str_) is not None
