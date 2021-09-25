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

from git import Repo
import os

from elf_diff.__init__ import __version__


def gitRepoInfo(settings):
    # If used from the git repo source tree
    repo_path = settings.module_path + "/../.."
    if not os.path.isdir(repo_path):
        return __version__

    try:
        repo = Repo(repo_path)
    except Exception:
        return __version__

    if not repo:
        return __version__

    try:
        return str(repo.head.reference.commit)
    except Exception:
        return __version__
