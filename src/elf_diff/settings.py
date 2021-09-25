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

import sys
import os
import shutil

from elf_diff.binary_pair import BinaryPairSettings
from elf_diff.error_handling import unrecoverableError
from elf_diff.error_handling import warning


class Parameter(object):
    def __init__(
        self,
        name,
        description,
        default=None,
        deprecated_alias=None,
        alias=None,
        no_cmd_line=False,
        is_flag=False,
    ):
        self.name = name
        self.description = description
        self.default = default
        self.alias = alias
        self.deprecated_alias = deprecated_alias
        self.no_cmd_line = no_cmd_line
        self.is_flag = is_flag


class Settings(object):
    def __init__(self, module_path):

        self.module_path = module_path

        self.setupParameters()

        self.presetDefaults()

        cmd_line_args = self.parseCommandLineArgs()

        if cmd_line_args.driver_file:

            self.driver_file = cmd_line_args.driver_file

            self.readDriverFile()

        self.considerCommandLineArgs(cmd_line_args)

        self.validateAndInitSettings()

    def setupParameters(self):

        self.parameters = [
            Parameter("old_binary_filename", "The old version of the elf binary."),
            Parameter("new_binary_filename", "The new version of the elf binary."),
            Parameter(
                "old_alias",
                "An alias string that is supposed to be used to reference the old binary version.",
            ),
            Parameter(
                "new_alias",
                "An alias string that is supposed to be used to reference the new binary version.",
            ),
            Parameter(
                "old_info_file",
                "A text file that contains information about the old binary version.",
            ),
            Parameter(
                "new_info_file",
                "A text file that contains information about the new binary version.",
            ),
            Parameter(
                "build_info",
                "A string that contains build information that is to be added to the report.",
                default="",
            ),
            Parameter(
                "bin_dir",
                "A place where the binutils live.",
                default=None,
            ),
            Parameter(
                "bin_prefix",
                "A prefix that is added to binutils executables.",
                deprecated_alias="bin-prefix",
                default="",
            ),
            Parameter(
                "objdump_command", "Full path to the objdump untility.", default=None
            ),
            Parameter("nm_command", "Full path to the nm untility.", default=None),
            Parameter("size_command", "Full path to the size untility.", default=None),
            Parameter(
                "html_file", "The filename of the generated single page HTML report."
            ),
            Parameter(
                "html_dir", "The directory of the generated multi page HTML report."
            ),
            Parameter("pdf_file", "The filename of the generated pdf report."),
            Parameter("project_title", "A project title to use for all reports."),
            Parameter(
                "driver_file",
                "A yaml file that contains settings and driver information.",
            ),
            Parameter(
                "driver_template_file",
                "A yaml file that is generated at the end of the run. It contains default parameters if no report was generated or, otherwise, the parameters that were read.",
            ),
            Parameter(
                "html_template_dir",
                "A directory that contains template html files. Defaults to elf_diff's own html directory.",
                no_cmd_line=True,
            ),
            Parameter(
                "mass_report",
                "Forces a mass report being generated. Otherwise the decision whether to generate a mass report is based on the binary_pairs found in the driver file.",
                default=False,
                is_flag=True,
            ),
            Parameter(
                "language",
                "A hint about the language that the elf was compiled from (choices: c++).",
                default="c++",
            ),
            Parameter(
                "similarity_threshold",
                "A threshold value between 0 and 1 above which two compared symbols are considered being similar",
                default=0.5,
            ),
            Parameter(
                "consider_equal_sized_identical",
                "If this flag is defined, symbols of equal size are considered as identical (and thus ignored in most cases).",
                default=False,
                is_flag=True,
            ),
            Parameter(
                "skip_details",
                "If this flag is defined, report details are displayed",
                default=False,
                is_flag=True,
            ),
            Parameter(
                "symbol_selection_regex",
                "A regex that is applied to select symbols to be considered for both, the old and the new elf file",
                default=None,
            ),
            Parameter(
                "symbol_selection_regex_old",
                "A regex that is applied to select symbols to be considered for the old elf file",
                default=None,
            ),
            Parameter(
                "symbol_selection_regex_new",
                "A regex that is applied to select symbols to be considered for the new elf file",
                default=None,
            ),
            Parameter(
                "symbol_exclusion_regex",
                "A regex that is applied to select symbols to be excluded for both, the old and the new elf file",
                default=None,
            ),
            Parameter(
                "symbol_exclusion_regex_old",
                "A regex that is applied to select symbols to be excluded for the old elf file",
                default=None,
            ),
            Parameter(
                "symbol_exclusion_regex_new",
                "A regex that is applied to select symbols to be excluded for the new elf file",
                default=None,
            ),
        ]

    def presetDefaults(self):

        self.mass_report_members = []

        for parameter in self.parameters:

            setattr(self, parameter.name, parameter.default)

    def deprecated(self, desc):
        return "{desc} [deprecated]".format(desc=desc)

    def parseCommandLineArgs(self):

        import argparse

        parser = argparse.ArgumentParser(
            description="Compares elf binaries and lists differences in symbol sizes, the disassemblies, etc."
        )

        for parameter in self.parameters:

            if parameter.no_cmd_line:
                continue

            if parameter.alias:
                param_name = parameter.alias
            else:
                param_name = parameter.name

            if parameter.is_flag:
                action = "store_true"
            else:
                action = "store"

            parser.add_argument(
                "--{name}".format(name=param_name),
                default=parameter.default,
                dest=parameter.name,
                action=action,
                help=parameter.description,
            )

            if parameter.deprecated_alias:
                parser.add_argument(
                    "--{name}".format(name=parameter.deprecated_alias),
                    default=parameter.default,
                    dest=parameter.name,
                    action=action,
                    help=parameter.description + " (deprecated)",
                )

        parser.add_argument(
            "binaries",
            nargs="*",
            default=None,
            help="The binaries to be compared (this is an alternative to --old_binary_filename and --new_binary_filename)",
        )

        actual_args = list()
        for arg_pos in range(1, len(sys.argv)):
            arg = sys.argv[arg_pos]
            if arg == "--":
                break
            actual_args.append(arg)

        return parser.parse_args(actual_args)

    def readDriverFile(self):

        import yaml

        my_yaml = None
        with open(self.driver_file, "r") as stream:
            try:
                my_yaml = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                unrecoverableError(exc)

        for parameter in self.parameters:

            if parameter.name in my_yaml.keys():

                setattr(self, parameter.name, my_yaml[parameter.name])

        # Read binary pairs

        if "binary_pairs" in my_yaml.keys():

            bin_pair_id = 1

            for data_set in my_yaml["binary_pairs"]:

                short_name = data_set.get("short_name")
                if not short_name:
                    unrecoverableError(
                        "No short_name defined for binary pair " + str(bin_pair_id)
                    )

                old_binary = data_set.get("old_binary")
                if not old_binary:
                    unrecoverableError(
                        "No old_binary defined for binary pair " + str(bin_pair_id)
                    )

                new_binary = data_set.get("new_binary")
                if not new_binary:
                    unrecoverableError(
                        "No new_binary defined for binary pair " + str(bin_pair_id)
                    )

                bp = BinaryPairSettings(short_name, old_binary, new_binary)

                self.mass_report_members.append(bp)

                bin_pair_id += 1

    def considerCommandLineArgs(self, cmd_line_args):

        for parameter in self.parameters:

            if parameter.no_cmd_line:
                continue

            if hasattr(cmd_line_args, parameter.name):
                value = getattr(cmd_line_args, parameter.name)

                if value != parameter.default:
                    setattr(self, parameter.name, value)

        if len(cmd_line_args.binaries) == 0:
            pass
        elif len(cmd_line_args.binaries) == 2:
            if self.old_binary_filename:
                unrecoverableError("Old binary filename redundantly defined")

            else:
                self.old_binary_filename = cmd_line_args.binaries[0]

            if self.new_binary_filename:
                unrecoverableError("Old binary filename redundantly defined")

            else:
                self.new_binary_filename = cmd_line_args.binaries[1]
        else:
            unrecoverableError("Please specify either none or two binaries")

    def findUntility(self, name):
        command_name = name + "_command"
        command = getattr(self, command_name)
        if command is not None:
            if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                return
            warning(f"Unable to find predefined {command_name} = {command}")

        if os.name == "nt":
            exe_extensions = [".exe", ""]
        else:
            exe_extensions = ["", ".exe"]

        for exe_extension in exe_extensions:
            basename = self.bin_prefix + name + exe_extension

            if self.bin_dir is not None:
                command = self.bin_dir + "/" + basename
                if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                    setattr(self, command_name, command)
                    return

        for exe_extension in exe_extensions:
            basename = self.bin_prefix + name + exe_extension
            command = shutil.which(basename)
            if (os.path.isfile(command)) and (os.access(command, os.X_OK)):
                setattr(self, command_name, command)
                return

        unrecoverableError(f"Unnable to find {name} command")

    def validateAndInitSettings(self):

        if self.old_binary_filename and not os.path.isfile(self.old_binary_filename):
            unrecoverableError(
                "Old binary '%s' is not a file or cannot be found"
                % (self.old_binary_filename)
            )

        if self.new_binary_filename and not os.path.isfile(self.new_binary_filename):
            unrecoverableError(
                "New binary '%s' is not a file or cannot be found"
                % (self.new_binary_filename)
            )

        self.findUntility("objdump")
        self.findUntility("nm")
        self.findUntility("size")

        if self.old_info_file:
            if os.path.isfile(self.old_info_file):
                with open(self.old_info_file, "r") as f:
                    self.old_binary_info = f.read()
            else:
                unrecoverableError(
                    "Unable to find old info file '%s'" % (self.old_info_file)
                )
        else:
            self.old_binary_info = ""

        if self.new_info_file:
            if os.path.isfile(self.new_info_file):
                with open(self.new_info_file, "r") as f:
                    self.new_binary_info = f.read()
            else:
                unrecoverableError(
                    "Unable to find new info file '%s'" % (self.new_info_file)
                )
        else:
            self.new_binary_info = ""

        if not self.old_alias:
            self.old_alias = self.old_binary_filename

        if not self.new_alias:
            self.new_alias = self.new_binary_filename

        print("Tools:")
        print(f"   objdump: {self.objdump_command}")
        print(f"   nm:      {self.nm_command}")
        print(f"   size:    {self.size_command}")

    def writeParameterTemplateFile(self, filename, output_actual_values=False):

        import datetime

        with open(filename, "w") as f:

            f.write("# This is an auto generated elf_diff driver file\n")
            f.write(
                "# Generated by elf_diff {date}\n".format(
                    date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            )
            f.write("\n")

            for parameter in self.parameters:

                if output_actual_values:
                    value = getattr(self, parameter.name)
                    if not value:
                        value = parameter.default

                else:
                    value = parameter.default

                f.write("# {desc}\n".format(desc=parameter.description))
                f.write("#\n")
                f.write('{name}: "{value}"\n'.format(name=parameter.name, value=value))
                f.write("\n")

    def isFirmwareBinaryDefined(self):
        return self.old_binary_filename or self.new_binary_filename
