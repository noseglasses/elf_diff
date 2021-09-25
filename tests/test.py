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
import subprocess
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--test_installed_package",
    action="store_true",
    help="Add this flag to enable testing using an installed elf_diff package",
)
parser.add_argument("unittest_args", nargs="*")

args = parser.parse_args()

# Now set the sys.argv to the unittest_args (leaving sys.argv[0] alone)
sys.argv[1:] = args.unittest_args

testing_dir = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))

if args.test_installed_package is True:
    elf_diff_start = [sys.executable, "-m", "elf_diff"]
else:
    bin_dir = testing_dir + "/../bin"
    elf_diff_start = [sys.executable, bin_dir + "/elf_diff"]

old_binary = testing_dir + "/libelf_diff_test_release_old.a"
new_binary = testing_dir + "/libelf_diff_test_release_new.a"
old_binary2 = testing_dir + "/libelf_diff_test_debug_old.a"
new_binary2 = testing_dir + "/libelf_diff_test_debug_new.a"

verbose_output = True


def runSubprocess(cmd, cwd=os.getcwd(), env=os.environ.copy()):

    if verbose_output:
        print("   Running command: {cmd}".format(cmd='"' + '" "'.join(cmd) + '"'))

    try:
        proc = subprocess.Popen(
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


class TestCommandLineArgs(unittest.TestCase):
    def test_pair_report(self):

        pdf_file = "pair_report_output.pdf"
        html_file = "pair_report_output.html"
        html_dir = "pair_report_multi_page"
        template_file = "output.tmpl.yml"

        [output, error] = runSubprocess(
            elf_diff_start
            + [
                "--old_binary_filename",
                old_binary,
                "--new_binary_filename",
                new_binary,
                "--old_alias",
                "an_old_alias",
                "--new_alias",
                "a_new_alias",
                "--old_info_file",
                testing_dir + "/old_binary_info.txt",
                "--new_info_file",
                testing_dir + "/new_binary_info.txt",
                "--build_info",
                "General build info",
                "--html_file",
                html_file,
                "--html_dir",
                html_dir,
                "--pdf_file",
                pdf_file,
                "--project_title",
                "Project title",
                "--driver_template_file",
                template_file,
            ]
        )

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driven_pair_report(self):

        driver_yaml_file = "pair_report.driver.yml"

        pdf_file = "driven_pair_report_output.pdf"
        html_file = "driven_pair_report_output.html"
        html_dir = "driven_pair_report_multi_page"
        template_file = "driven_pair_report_output.tmpl.yml"

        with open(driver_yaml_file, "w") as f:

            f.write("old_binary_filename: " + old_binary + "\n")
            f.write("new_binary_filename: " + new_binary + "\n")
            f.write("old_alias: " + "an_old_alias\n")
            f.write("new_alias: " + "a_new_alias\n")
            f.write("old_info_file: " + testing_dir + "/old_binary_info.txt\n")
            f.write("new_info_file: " + testing_dir + "/new_binary_info.txt\n")
            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: " + html_file + "\n")
            f.write("html_dir: " + html_dir + "\n")
            f.write("pdf_file: " + pdf_file + "\n")
            f.write("project_title: " + "Project title\n")
            f.write("driver_template_file: " + template_file + "\n")

        [output, error] = runSubprocess(
            elf_diff_start + ["--driver_file", driver_yaml_file]
        )

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))

    def test_driven_mass_report(self):

        driver_yaml_file = "mass_report.driver.yml"

        pdf_file = "driven_mass_report_output.pdf"
        html_file = "driven_mass_report_output.html"
        template_file = "driven_mass_report_output.tmpl.yml"

        with open(driver_yaml_file, "w") as f:

            f.write("build_info: >\n")
            f.write("  Build info.\n")
            f.write("  More build info.\n")
            f.write("html_file: " + html_file + "\n")
            f.write("pdf_file: " + pdf_file + "\n")
            f.write("project_title: " + "Project title\n")
            f.write("driver_template_file: " + template_file + "\n")

            f.write("binary_pairs:\n")
            f.write('    - old_binary: "' + old_binary + '"\n')
            f.write('      new_binary: "' + new_binary + '"\n')
            f.write('      short_name: "First binary name"\n')
            f.write('    - old_binary: "' + old_binary2 + '"\n')
            f.write('      new_binary: "' + new_binary2 + '"\n')
            f.write('      short_name: "Second binary name"\n')

        [output, error] = runSubprocess(
            elf_diff_start + ["--driver_file", driver_yaml_file]
        )

        # Check if all output files exist
        #
        self.assertTrue(os.path.isfile(pdf_file))
        self.assertTrue(os.path.isfile(html_file))
        self.assertTrue(os.path.isfile(template_file))


if __name__ == "__main__":
    unittest.main()
