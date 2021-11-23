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
from elf_diff.error_handling import warning

from typing import List, Optional, Dict
import os
import shutil


class Binutils(object):
    COMMANDS = ["objdump", "nm", "readelf", "size"]

    def __init__(self):
        self.objdump_command: Optional[str] = None
        self.nm_command: Optional[str] = None
        self.readelf_command: Optional[str] = None
        self.size_command: Optional[str] = None

        self._bin_prefix: str = ""
        self.is_functional = True

    def _findUtilityInBinDir(
        self, name: str, exe_extensions: List[str]
    ) -> Optional[str]:
        for exe_extension in exe_extensions:
            basename: str = self._bin_prefix + name + exe_extension

            if self._bin_dir is not None:
                command = os.path.join(self._bin_dir, basename)
                if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                    return command
        return None

    def _findUtilityUsingWhich(
        self, name: str, exe_extensions: List[str]
    ) -> Optional[str]:
        for exe_extension in exe_extensions:
            basename = self._bin_prefix + name + exe_extension
            command = shutil.which(basename)
            if (
                (command is not None)
                and (os.path.isfile(command))
                and (os.access(command, os.X_OK))
            ):
                return command
        return None

    def findUtility(self, name: str) -> None:
        """Find a utility and set a attribute of this class to the path of the utility executable"""
        command_name: str = name + "_command"
        command: Optional[str] = getattr(self, command_name)
        if command is not None:
            if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                return
            warning(f"Unable to find predefined {command_name} = {command}")

        exe_extensions: List[str]
        if os.name == "nt":
            exe_extensions = [".exe", ""]
        else:
            exe_extensions = ["", ".exe"]

        command = self._findUtilityInBinDir(name, exe_extensions)

        if command is not None:
            setattr(self, command_name, command)
            return

        command = self._findUtilityUsingWhich(name, exe_extensions)

        if command is not None:
            setattr(self, command_name, command)
            return

        raise Exception(f"Unnable to find {name} command")

    def initialize(
        self, associate: Dict, bin_prefix: Optional[str], bin_dir: Optional[str]
    ):

        self._bin_prefix = bin_prefix or self._bin_prefix
        self._bin_dir = bin_dir

        for command in Binutils.COMMANDS:
            attr_name = "%s_command" % command
            setattr(self, attr_name, associate.get(attr_name, None))

        self.findUtility("objdump")
        self.findUtility("nm")
        self.findUtility("readelf")
        self.findUtility("size")

        print("Tools:")
        print(f"   objdump: {self.objdump_command}")
        print(f"   nm:      {self.nm_command}")
        print(f"   readelf:      {self.readelf_command}")
        print(f"   size:    {self.size_command}")
