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

import elf_diff.html as html


class Report(object):
    def getSinglePageScriptContent(self):
        sortable_js_file = self.settings.module_path + "/html/js/sorttable.js"
        sortable_js_content = None
        with open(sortable_js_file, "r", encoding="ISO-8859-1") as file:
            sortable_js_content = "<script>\n%s\n</script>\n" % html.escapeString(
                file.read()
            )

        elf_diff_general_css_file = (
            self.settings.module_path + "/html/css/elf_diff_general.css"
        )
        elf_diff_general_css_content = None
        with open(elf_diff_general_css_file, "r") as file:
            elf_diff_general_css_content = (
                "<style>\n%s\n</style>\n" % html.escapeString(file.read())
            )

        return sortable_js_content, elf_diff_general_css_content
