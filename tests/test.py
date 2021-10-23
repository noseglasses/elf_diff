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

import unittest
import os
import inspect
import subprocess  # nosec # silence bandid warning
import sys
import argparse

bin_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))

sys.path.append(bin_path + "/../src")

from elf_diff.settings import parameters

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--test_installed_package",
    action="store_true",
    help="Add this flag to enable testing using an installed elf_diff package",
)
parser.add_argument(
    "-c",
    "--enable_code_coverage",
    action="store_true",
    help="Add this flag to enable coverage generation",
)
parser.add_argument("unittest_args", nargs="*")

args = parser.parse_args()

# Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
sys.argv[1:] = args.unittest_args

testing_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))

if args.test_installed_package is True:
    elf_diff_start = [sys.executable, "-m", "elf_diff"]
else:
    bin_dir = os.path.join(testing_dir, "..", "bin")
    if args.enable_code_coverage is True:
        elf_diff_start = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--parallel-mode",  # Creates individual .coverage* files for each run
            os.path.join(bin_dir, "elf_diff"),
        ]
    else:
        elf_diff_start = [sys.executable, os.path.join(bin_dir, "elf_diff")]

old_binary_x86_64 = os.path.join(testing_dir, "libelf_diff_test_release_old.a")
new_binary_x86_64 = os.path.join(testing_dir, "libelf_diff_test_release_new.a")
old_binary2_x86_64 = os.path.join(testing_dir, "libelf_diff_test_debug_old.a")
new_binary2_x86_64 = os.path.join(testing_dir, "libelf_diff_test_debug_new.a")

old_binary_arm = os.path.join(testing_dir, "libelf_diff_test_release_old-arm.a")
new_binary_arm = os.path.join(testing_dir, "libelf_diff_test_release_new-arm.a")

verbose_output = True


def prepareArgsAvailable():
    args_available = set()
    for parameter in parameters:
        args_available.add(parameter.name)
    return args_available


class ArgsWatcher(object):
    def __init__(self):

        self.args_available = prepareArgsAvailable()
        self.args_tested = set()

    def prepareArgs(self, args_dict):
        args_list = []
        for key, value in args_dict.items():
            self.args_tested.add(key)
            args_list.append(f"--{key}")
            if value is not None:
                args_list.append(value)

        return args_list

    def testIfAllArgsUsedAtLeastOnce(self):
        """Test if all elf_diff command line args are at least used once while testing"""

        print("Args available: " + str(len(self.args_available)))
        print("Args tested: " + str(len(self.args_tested)))
        args_not_tested = self.args_available - self.args_tested

        if len(args_not_tested) > 0:
            print("Command line args not tested:")
            for arg_not_tested in sorted(args_not_tested):
                print(f"   {arg_not_tested}")

        assert len(args_not_tested) == 0

    def listArgs(self):
        print("Command line args available:")
        for arg in sorted(self.args_available):
            print(f"   {arg}")

    def exportTestSkeletons(self):
        for arg in sorted(self.args_available):
            print(f"   def test_{arg}(self):")
            print("       pass")
            print("")


args_watcher = ArgsWatcher()


def runSubprocess(cmd, cwd=None, env=None):

    if cwd is None:
        cwd = os.getcwd()

    if env is None:
        env = os.environ.copy()

    if verbose_output:
        print("   Running command: {cmd}".format(cmd='"' + '" "'.join(cmd) + '"'))

    try:
        proc = subprocess.Popen(  # nosec # silence bandid warning
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env
        )

        o, e = proc.communicate()

        rc = proc.returncode

        output = o.decode("utf8")
        error = e.decode("utf8")

    except (OSError) as e:
        print(e)
        sys.exit(1)

    if rc != 0:
        print("Failed running command %s in directory %s failed" % (str(cmd), cwd))
        print("   exit code: %d" % (rc))
        print("   stdout: %s" % (output))
        print("   stderr: %s" % (error))
        sys.exit(1)

    if verbose_output:
        print("      exit code: %d" % (rc))
        if len(output) > 0:
            print("      stdout: %s" % (output))

        if len(error) > 0:
            print("      stderr: %s" % (error))

    return [output, error]


def runElfDiff(args_dict):
    """Runs elf diff with a given set of arguments

    args_dict: Argument dict. Flag argmuents require None type values
    """
    args_list = args_watcher.prepareArgs(args_dict)
    [output, error] = runSubprocess(  # pylint: disable=unused-variable
        elf_diff_start + args_list
    )


def runSimpleTest(args_dict):
    """Runs a simple test with a set of arguments"""
    actual_args_dict = args_dict
    actual_args_dict["old_binary_filename"] = old_binary_x86_64
    actual_args_dict["new_binary_filename"] = new_binary_x86_64
    runElfDiff(actual_args_dict)


def runSimpleTestArm(args_dict):
    """Runs a simple test with a set of arguments"""
    actual_args_dict = args_dict
    actual_args_dict["old_binary_filename"] = old_binary_arm
    actual_args_dict["new_binary_filename"] = new_binary_arm
    runElfDiff(actual_args_dict)


class TestCommandLineArgs(unittest.TestCase):
    def test_bin_dir(self):  # pylint: disable=no-self-use
        runSimpleTest({"bin_dir": "/usr/bin"})

    def test_bin_prefix(self):  # pylint: disable=no-self-use
        runSimpleTestArm({"bin_prefix": "arm-linux-gnueabi-"})

    def test_build_info(self):  # pylint: disable=no-self-use
        runSimpleTest({"build_info": "Some buildinfo string"})

    def test_consider_equal_sized_identical(self):  # pylint: disable=no-self-use
        runSimpleTest({"consider_equal_sized_identical": None})

    def test_driver_file1(self):

        driver_yaml_file = "pair_report.driver.yml"

        pdf_file = "driven_pair_report_output.pdf"
        html_file = "driven_pair_report_output.html"
        html_dir = "driven_pair_report_multi_page"
        template_file = "driven_pair_report_output.tmpl.yml"

        with open(driver_yaml_file, "w") as f:

            f.write("old_binary_filename: '" + old_binary_x86_64 + "'\n")
            f.write("new_binary_filename: '" + new_binary_x86_64 + "'\n")
            f.write("old_alias: " + "an_old_alias\n")
            f.write("new_alias: " + "a_new_alias\n")
            f.write(
                "old_info_file: '"
                + os.path.join(testing_dir, "old_binary_info.txt")
                + "'\n"
            )
            f.write(
                "new_info_file: '"
                + os.path.join(testing_dir, "new_binary_info.txt")
                + "'\n"
            )
            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: '" + html_file + "'\n")
            f.write("html_dir: '" + html_dir + "'\n")
            f.write("pdf_file: '" + pdf_file + "'\n")
            f.write("project_title: '" + "Project title'\n")
            f.write("driver_template_file: '" + template_file + "'\n")

        runElfDiff({"driver_file": driver_yaml_file})

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driver_file2(self):

        driver_yaml_file = "mass_report.driver.yml"

        pdf_file = "driven_mass_report_output.pdf"
        html_file = "driven_mass_report_output.html"
        template_file = "driven_mass_report_output.tmpl.yml"

        with open(driver_yaml_file, "w") as f:

            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: '" + html_file + "'\n")
            f.write("pdf_file: '" + pdf_file + "'\n")
            f.write("project_title: 'Project title'\n")
            f.write("driver_template_file: '" + template_file + "'\n")

            f.write("binary_pairs:\n")
            f.write("    - old_binary: '" + old_binary_x86_64 + "'\n")
            f.write("      new_binary: '" + new_binary_x86_64 + "'\n")
            f.write("      short_name: 'First binary name'\n")
            f.write("    - old_binary: '" + old_binary2_x86_64 + "'\n")
            f.write("      new_binary: '" + new_binary2_x86_64 + "'\n")
            f.write("      short_name: 'Second binary name'\n")

        runElfDiff({"driver_file": driver_yaml_file})

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driver_template_file(self):
        driver_template_file = "driver_template.yml"
        runSimpleTest({"driver_template_file": driver_template_file})
        self.assertTrue(os.path.isfile(driver_template_file))

    def test_html_dir(self):
        html_dir = "parameter_test_multi_page_pair_report"
        runSimpleTest({"html_dir": html_dir})
        self.assertTrue(os.path.isdir(html_dir))

    def test_html_file(self):
        html_file = "parameter_test_single_page_pair_report.html"
        runSimpleTest({"html_file": html_file})
        self.assertTrue(os.path.isfile(html_file))

    def test_html_template_dir(self):
        pass

    def test_language(self):
        pass

    def test_mass_report(self):
        pass

    def test_new_alias(self):  # pylint: disable=no-self-use
        runSimpleTest({"new_alias": "New alias"})

    def test_new_binary_filename(self):
        # This is already tested by all simple tests
        pass

    def test_new_info_file(self):
        pass

    def test_new_mangling_file(self):
        pass

    def test_nm_command(self):  # pylint: disable=no-self-use
        runSimpleTest({"nm_command": "/usr/bin/nm"})

    def test_objdump_command(self):  # pylint: disable=no-self-use
        runSimpleTest({"nm_command": "/usr/bin/objdump"})

    def test_old_alias(self):  # pylint: disable=no-self-use
        runSimpleTest({"old_alias": "Old alias"})

    def test_old_binary_filename(self):
        # This is already tested by all simple tests
        pass

    def test_old_info_file(self):
        pass

    def test_old_mangling_file(self):
        pass

    def test_pdf_file(self):
        pdf_file = "parameter_test_single_page_pair_report.pdf"
        runSimpleTest({"pdf_file": pdf_file})
        self.assertTrue(os.path.isfile(pdf_file))

    def test_project_title(self):  # pylint: disable=no-self-use
        runSimpleTest({"project_title": "A Project"})

    def test_similarity_threshold(self):  # pylint: disable=no-self-use
        runSimpleTest({"similarity_threshold": "0.5"})

    def test_size_command(self):  # pylint: disable=no-self-use
        runSimpleTest({"nm_command": "/usr/bin/size"})

    def test_skip_details(self):  # pylint: disable=no-self-use
        runSimpleTest({"skip_details": None})

    def test_skip_symbol_similarities(self):  # pylint: disable=no-self-use
        runSimpleTest({"skip_symbol_similarities": None})

    def test_symbol_exclusion_regex(self):
        pass

    def test_symbol_exclusion_regex_new(self):
        pass

    def test_symbol_exclusion_regex_old(self):
        pass

    def test_symbol_selection_regex(self):
        pass

    def test_symbol_selection_regex_new(self):
        pass

    def test_symbol_selection_regex_old(self):
        pass


if __name__ == "__main__":
    unittest.main(exit=False)
    # args_watcher.exportTestSkeletons()
    # args_watcher.testIfAllArgsUsedAtLeastOnce()
