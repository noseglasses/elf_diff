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
import re

# import shutil

bin_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))

root_dir = os.path.join(bin_path, "..")

sys.path.append(os.path.join(root_dir, "src"))

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

args, unittest_args = parser.parse_known_args()

# Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
sys.argv[1:] = unittest_args

testing_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))

if args.test_installed_package is True:
    elf_diff_start = [sys.executable, "-m", "elf_diff"]
else:
    bin_dir = os.path.join(testing_dir, "..", "bin")
    if args.enable_code_coverage is True:
        print("Running with coverage testing")
        elf_diff_start = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            "--branch",
            "--parallel-mode",  # Creates individual .coverage* files for each run
            os.path.join(bin_dir, "elf_diff"),
        ]
    else:
        elf_diff_start = [sys.executable, os.path.join(bin_dir, "elf_diff")]

old_binary_x86_64 = os.path.join(
    testing_dir, "x86_64", "libelf_diff_test_release_old.a"
)
new_binary_x86_64 = os.path.join(
    testing_dir, "x86_64", "libelf_diff_test_release_new.a"
)
old_binary2_x86_64 = os.path.join(testing_dir, "x86_64", "libelf_diff_test_debug_old.a")
new_binary2_x86_64 = os.path.join(testing_dir, "x86_64", "libelf_diff_test_debug_new.a")

old_binary_arm = os.path.join(testing_dir, "arm", "libelf_diff_test_release_old.a")
new_binary_arm = os.path.join(testing_dir, "arm", "libelf_diff_test_release_new.a")

old_binary_ghs = os.path.join(testing_dir, "ghs", "libelf_diff_test_release_old.a")
new_binary_ghs = os.path.join(testing_dir, "ghs", "libelf_diff_test_release_new.a")

old_mangling_file_ghs = os.path.join(
    testing_dir, "ghs", "libelf_diff_test_release_old.a.demangle.txt"
)
new_mangling_file_ghs = os.path.join(
    testing_dir, "ghs", "libelf_diff_test_release_new.a.demangle.txt"
)

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

    def prepareArgs(self, args_list):
        output_args_list = []
        for args_tuple in args_list:
            key = args_tuple[0]
            value = args_tuple[1]
            self.args_tested.add(key)
            output_args_list.append(f"--{key}")
            if value is not None:
                output_args_list.append(value)

        return output_args_list

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


def runElfDiff(args_list):
    """Runs elf diff with a given set of arguments

    args_list: Arguments are given as name value pair tuples. Flag argmuments require None type values
    """
    prepared_args_list = args_watcher.prepareArgs(args_list)
    [output, error] = runSubprocess(  # pylint: disable=unused-variable
        elf_diff_start + prepared_args_list
    )


class TestCaseWithSubdirs(unittest.TestCase):
    @staticmethod
    def _setUpScoped(scope, directory):
        scope.old_pwd = os.getcwd()
        if not os.path.exists(directory):
            os.mkdir(directory)
        os.chdir(directory)

    @staticmethod
    def _tearDownScoped(scope):
        os.chdir(scope.old_pwd)

    @classmethod
    def setUpClass(cls):
        TestCaseWithSubdirs._setUpScoped(cls, cls.__name__)

    @classmethod
    def tearDownClass(cls):
        TestCaseWithSubdirs._tearDownScoped(cls)

    def setUp(self):
        test_function_full_id = self.id()
        # Just take the final portion of the test id after the final period
        test_name_re = re.compile(r".*\.(\w*)")
        m = test_name_re.match(test_function_full_id)
        if m is None:
            print("Strange test name")
            sys.exit(1)
        test_dir = m.group(1)
        TestCaseWithSubdirs._setUpScoped(self, test_dir)

    def tearDown(self):
        TestCaseWithSubdirs._tearDownScoped(self)


class TestCommandLineArgs(TestCaseWithSubdirs):
    def runSimpleTestBase(
        self,
        args_list,
        old_binary_filename=old_binary_x86_64,
        new_binary_filename=new_binary_x86_64,
        output_file=None,
    ):
        """Runs a simple test with a set of arguments"""
        actual_args_list = args_list
        actual_args_list.append(("old_binary_filename", old_binary_filename))
        actual_args_list.append(("new_binary_filename", new_binary_filename))
        runElfDiff(actual_args_list)
        if output_file is not None:
            self.assertTrue(os.path.isfile(output_file))

    def runSimpleTest(self, args_list):
        """Runs a simple test with a set of arguments"""
        html_file = "single_page_report.html"
        actual_args_list = args_list
        actual_args_list.append(("html_file", html_file))
        self.runSimpleTestBase(args_list=actual_args_list, output_file=html_file)

    def runSimpleTest2(self, args_list):
        """Runs a simple test with a set of arguments"""
        html_file = "single_page_report.html"
        actual_args_list = args_list
        actual_args_list.append(("html_file", html_file))
        self.runSimpleTestBase(
            args_list=actual_args_list,
            old_binary_filename=old_binary2_x86_64,
            new_binary_filename=new_binary2_x86_64,
            output_file=html_file,
        )

    def runSimpleTestArm(self, args_list):
        """Runs a simple test with a set of arguments"""
        html_file = "single_page_report.html"
        actual_args_list = args_list
        actual_args_list.append(("html_file", html_file))
        self.runSimpleTestBase(
            args_list=actual_args_list,
            old_binary_filename=old_binary_arm,
            new_binary_filename=new_binary_arm,
            output_file=html_file,
        )

    def runSimpleTestGhs(self, args_list):
        """Runs a simple test with a set of arguments"""
        html_file = "single_page_report.html"
        actual_args_list = args_list
        actual_args_list.append(("html_file", html_file))
        self.runSimpleTestBase(
            args_list=actual_args_list,
            old_binary_filename=old_binary_ghs,
            new_binary_filename=new_binary_ghs,
            output_file=html_file,
        )

    def test_bin_dir(self):
        self.runSimpleTest([("bin_dir", "/usr/bin")])

    def test_bin_prefix1(self):
        self.runSimpleTestArm([("bin_prefix", "arm-linux-gnueabi-")])

    @unittest.expectedFailure
    def test_bin_prefix2(self):
        self.runSimpleTestArm([("bin_prefix", "___bad_prefix___")])

    def test_build_info(self):
        self.runSimpleTest([("build_info", "Some buildinfo string")])

    def test_consider_equal_sized_identical(self):
        self.runSimpleTest([("consider_equal_sized_identical", None)])

    def test_driver_file(self):

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

        runElfDiff([("driver_file", driver_yaml_file)])

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driver_template_file(self):
        driver_template_file = "driver_template.yml"
        self.runSimpleTest([("driver_template_file", driver_template_file)])
        self.assertTrue(os.path.isfile(driver_template_file))

    def test_dump_document_structure(self):
        self.runSimpleTest([("dump_document_structure", None)])

    def test_html_dir(self):
        html_dir = "parameter_test_multi_page_pair_report"
        self.runSimpleTestBase([("html_dir", html_dir)])
        self.assertTrue(os.path.isdir(html_dir))

    def test_html_file(self):  # pylint: disable=no-self-use
        # Already tested by all simple tests
        pass

    def test_html_template_dir(self):
        # Parameter currently not exported
        # source_template_path = os.path.join(root_dir, "src", "elf_diff", "html")
        # target_template_path = "template_copy"
        # shutil.copytree(source_template_path, target_template_path)
        # self.runSimpleTest([("html_template_dir": target_template_path})
        pass

    def test_json_file(self):
        self.runSimpleTest([("json_file", "output.json")])

    def test_language1(self):
        self.runSimpleTest([("language", "c++")])

    @unittest.expectedFailure
    def test_language2(self):
        self.runSimpleTest([("language", "___unknown___")])

    def test_load_plugin(self):
        self.runSimpleTest(
            [
                (
                    "load_plugin",
                    "$HOME/Documents/elf_diff/tests/plugin/test_plugin.py;TestExportPairReportPlugin;foo=bar;zoo=zar",
                )
            ]
        )

    def test_mass_report(self):

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

        runElfDiff([("driver_file", driver_yaml_file)])

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_new_alias(self):
        self.runSimpleTest([("new_alias", "New alias")])

    def test_new_binary_filename(self):  # pylint: disable=no-self-use
        # This is already tested by all simple tests
        pass

    def test_new_info_file(self):
        new_info_file = "new_info.txt"
        with open(new_info_file, "w") as f:
            f.write("Some additional new info")
        self.runSimpleTest([("new_info_file", new_info_file)])

    def test_new_mangling_file(self):
        self.runSimpleTestGhs([("new_mangling_file", new_mangling_file_ghs)])

    def test_nm_command(self):
        self.runSimpleTest([("nm_command", "/usr/bin/nm")])

    def test_objdump_command(self):
        self.runSimpleTest([("nm_command", "/usr/bin/objdump")])

    def test_old_alias(self):
        self.runSimpleTest([("old_alias", "Old alias")])

    def test_old_binary_filename(self):  # pylint: disable=no-self-use
        # This is already tested by all simple tests
        pass

    def test_old_info_file(self):
        old_info_file = "old_info.txt"
        with open(old_info_file, "w") as f:
            f.write("Some additional old info")
        self.runSimpleTest([("old_info_file", old_info_file)])

    def test_old_mangling_file(self):
        self.runSimpleTestGhs([("old_mangling_file", old_mangling_file_ghs)])

    def test_pdf_file(self):
        pdf_file = "parameter_test_single_page_pair_report.pdf"
        self.runSimpleTestBase([("pdf_file", pdf_file)])
        self.assertTrue(os.path.isfile(pdf_file))

    def test_project_title(self):
        self.runSimpleTest([("project_title", "A Project")])

    def test_similarity_threshold(self):
        self.runSimpleTest([("similarity_threshold", "0.5")])

    def test_size_command(self):
        self.runSimpleTest([("nm_command", "/usr/bin/size")])

    def test_skip_details(self):
        self.runSimpleTest([("skip_details", None)])

    def test_skip_symbol_similarities(self):
        self.runSimpleTest([("skip_symbol_similarities", None)])

    def test_symbol_exclusion_regex(self):
        self.runSimpleTest2([("symbol_exclusion_regex", ".*IStay.*")])

    def test_symbol_exclusion_regex_new(self):
        self.runSimpleTest2([("symbol_exclusion_regex_new", ".*IStay.*")])

    def test_symbol_exclusion_regex_old(self):
        self.runSimpleTest2([("symbol_exclusion_regex_old", ".*IStay.*")])

    def test_symbol_selection_regex(self):
        self.runSimpleTest2([("symbol_selection_regex", ".*IStay.*")])

    def test_symbol_selection_regex_new(self):
        self.runSimpleTest2([("symbol_selection_regex_new", ".*IStay.*")])

    def test_symbol_selection_regex_old(self):
        self.runSimpleTest2([("symbol_selection_regex_old", ".*IStay.*")])

    def test_txt_file(self):
        self.runSimpleTest([("txt_file", "output.txt")])

    def test_yaml_file(self):
        self.runSimpleTest([("yaml_file", "output.yaml")])


if __name__ == "__main__":
    unittest.main(exit=False)
    # args_watcher.exportTestSkeletons()
    # args_watcher.testIfAllArgsUsedAtLeastOnce()
