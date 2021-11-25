# -*- coding: utf-8 -*-

# -*- mode: python -*-
#
# elf_diff
#
# Copyright (C) 2021  Noseglasses (shinynoseglasses@gmail.com)
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
from elf_diff.formatted_output import SEPARATOR
import elf_diff.formatted_output as fo

from typing import List, Optional, Tuple, Dict
import os
import sys
import subprocess  # nosec # silence bandid warning

VERBOSE_OUTPUT = True


def __formatCommandResults(rc: int, output: str, error: str) -> str:
    o = ""
    o += f"exit code: {rc}\n"
    if output == "":
        o += "nothing written to stdout\n"
    else:
        o += "stdout:\n"
        o += f"{fo.START_CITATION}\n"
        o += f"{output}\n"
        o += f"{fo.END_CITATION}\n"
    if error == "":
        o += "nothing written to stderr\n"
    else:
        o += "stderr:\n"
        o += f"{fo.START_CITATION}\n"
        o += f"{error}\n"
        o += f"{fo.END_CITATION}\n"

    return o


def runSubprocess(
    test_name: str,
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    expected_return_code=0,
) -> Tuple[str, str]:

    if cwd is None:
        cwd = os.getcwd()

    if env is None:
        env = os.environ.copy()

    if VERBOSE_OUTPUT:
        print(SEPARATOR)
        print(f"Test {test_name}")
        print(SEPARATOR)
        sys.stdout.write(f'"{cmd[0]}" ')
        for cmd_line_param in cmd[1:]:
            if cmd_line_param.startswith("--"):
                sys.stdout.write("\\\n   ")
            sys.stdout.write(f'"{cmd_line_param}" ')
        sys.stdout.write("\n")

    rc: int = -1
    output: str = ""
    error: str = ""
    try:
        proc = subprocess.Popen(  # nosec # silence bandid warning
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env
        )

        o, e = proc.communicate()

        rc = proc.returncode

        output = o.decode("utf8")
        error = e.decode("utf8")

    except (OSError) as e:
        err_str = f"{SEPARATOR}\n"
        err_str += f"{e}\n"
        err_str += f"Failed running command in directory '{cwd}'\n"
        err_str += __formatCommandResults(rc, output, error)
        raise Exception(err_str)
        # sys.exit(1)

    if rc != expected_return_code:
        err_str = f"{SEPARATOR}\n"
        err_str += "Encountered an unexpected return code\n"
        err_str += f"expected return code: {expected_return_code}\n"
        err_str += __formatCommandResults(rc, output, error)
        raise Exception(err_str)
        # sys.exit(1)

    if VERBOSE_OUTPUT:
        print(SEPARATOR)
        print(__formatCommandResults(rc, output, error))
        print(SEPARATOR)

    return (output, error)
