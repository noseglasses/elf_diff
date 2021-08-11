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
   
unknown_version = "<unknown version>"
   
def gitRepoInfo(settings):
   if not os.path.isdir(settings.repo_path):
      return unknown_version
   
   repo = Repo(settings.repo_path)
   
   if not repo:
      return unknown_version
   
   try:
      return str(repo.head.reference.commit)
   except:
      return unknown_version
