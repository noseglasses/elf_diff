[![PyPi version](https://badgen.net/pypi/v/elf_diff/)](https://pypi.org/project/elf_diff)
[![PyPi license](https://badgen.net/pypi/license/elf_diff/)](https://pypi.org/project/elf_diff/)
![Python Versions](https://img.shields.io/pypi/pyversions/elf_diff.svg?style=flat)
![Code style black](https://img.shields.io/badge/code%20style-black-black)
[![codecov](https://codecov.io/gh/noseglasses/elf_diff/branch/master/graph/badge.svg?token=4A71C5ZYM9)](https://codecov.io/gh/noseglasses/elf_diff)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/08f1e1dd9e3240799be5470e86ad5a58)](https://www.codacy.com/gh/noseglasses/elf_diff/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=noseglasses/elf_diff&amp;utm_campaign=Badge_Grade)

![check code formatting](https://github.com/noseglasses/elf_diff/actions/workflows/black_code_formatting.yml/badge.svg)
![type checking](https://github.com/noseglasses/elf_diff/actions/workflows/type_checking_mypy.yml/badge.svg)
![CodeQL analysis](https://github.com/noseglasses/elf_diff/actions/workflows/codeql-analysis.yml/badge.svg)
![lint generated html](https://github.com/noseglasses/elf_diff/actions/workflows/lint_generated_html.yml/badge.svg)
![lint python](https://github.com/noseglasses/elf_diff/actions/workflows/lint_python_flake8.yml/badge.svg)
![lint documentation](https://github.com/noseglasses/elf_diff/actions/workflows/lint_README.yml/badge.svg)
![build](https://github.com/noseglasses/elf_diff/actions/workflows/local_package_build.yml/badge.svg)
![package installation](https://github.com/noseglasses/elf_diff/actions/workflows/venv_local_package_install.yml/badge.svg)
![test](https://github.com/noseglasses/elf_diff/actions/workflows/run_tests.yml/badge.svg)
![deploy](https://github.com/noseglasses/elf_diff/actions/workflows/package_deploy.yml/badge.svg)

<h1><img style="vertical-align:middle" src="https://github.com/noseglasses/elf_diff/blob/bb703f85ea24c7ee27998bb6b3e554843f31248c/images/favicon.png"> elf_diff - A Tool to Compare Elf Binaries</h1>

## Introduction

This tool compares pairs of ELF binary files and provides information about differences in the contained symbols with respect to the space that they occupy in program memory (functions and global data) and in RAM (global data). Binary pairs that are passed to _elf_diff_ are typically two versions of the same program/library/firmware. _elf_diff_ can help you to find out about the impact of your changes on your code's resource consumption.

The differences between the binaries are summarized in tables that contain information about persisting, disappeared and new symbols. _elf_diff_ also attempts to find pairs of matching symbols that might have been subject to renaming or signature changes (modified function arguments). Please be warned that the means to determine such symbol relations are very limited when working with binaries. False positives will result.

For all those symbols that have been subject to changes and also for the new and disappeared symbols, the tool provides diff-like comparisons of the disassembly.

The following types of output files are currently supported: HTML, PDF, YAML, JSON, XML, TXT.

HTML documents are cross-linked to conveniently allow jumping back and forth between bits of information, e.g. tabular information and symbol disassemblies. Du to the potentially large amount of information, some parts of the HTML reports are ommitted in the pdf files.

_elf_diff_ has two modes of operation, pair-reports and mass-reports. While the former compares two binaries, the latter generates an overview-report for a set of binary-pairs. Such overview-reports list only the changes in terms of symbol sizes and the amount of symbols, no disassembly is provided to gain feasible document sizes.

### Example

Assume you have two compiled versions of a software and you might be interested in the most prominent differences (and possibly the similarities) between both.

One way of comparing binaries is looking at the contained [symbols](https://en.wikipedia.org/wiki/Symbol_table). This is what _elf_diff_ does.

Let's start with exploring how differences in source code reflect in the symbols being created. 

For example, the following two C++ code snippets come with some subtle differences:

<table>
<tr>
<th> Version 1 (old) </th>
<th> Version 2 (new) </th>
</tr>
<tr>
<td>

```cpp
int func(int a) {
   return 42;
}

int var = 17;

class Test {
   public:
      
      static int f(int a, int b);
      int g(float a, float b);
      
   protected:
      
      static int m_;
};

int Test::f(int a, int b) { return 42; }
int Test::g(float a, float b) { return 1; }

int Test::m_ = 13;

int persisting1(int a) { return 43; }
int persisting2(int a) { return 43; }
```

</td>
<td>

```cpp
int func(double a) {
   return 42;
}

int var = 17;

class Test1 {
   public:
      
      static int f(int a, int b);
      int g(float a, float b);
      
   protected:
      
      static int m_;
};

int Test1::f(int a, int b) { return 42; }
int Test1::g(float a, float b) { return 1; }

int Test1::m_ = 13;

int persisting1(int a) { return 42; }
int persisting2(int a) { return 42; }
```

</td>
</tr>
</table>

Compiled and linked version of the two above code snippets can be found in the plaform specific subdirectories of the `tests` subdirectory of _elf_diff_ git repository. To generate a multi page pair report from these files, please install the _elf_diff_ Python packages as described in the installation section of this document. Then enter the following in a console on a Linux system. Please replace the placeholder `<elf_diff sandbox>` with the absolute path of your local _elf_diff_ sandbox.

```sh
python3 -m elf_diff --html_dir report <elf_diff sandbox>/tests/x86_64/libelf_diff_test_debug_old.a <elf_diff sandbox>/tests/x86_64/libelf_diff_test_debug_new.a
```

By means of its self contained HTML reports _elf_diff_ allows for conveniently analyzing the similarities and differences between the symbols contained
in [elf](https://en.wikipedia.org/wiki/Executable_and_Linkable_Format) files.

Please click on the table headers to proceed to the HTML pages that _elf_diff_ generated based on the above code example.

[Multi Page](https://noseglasses.github.io/elf_diff/examples/simple/pair_report_multi_page/index.html)                 |  [Single Page](https://noseglasses.github.io/elf_diff/examples/simple/pair_report_output.html)
:-------------------------:|:-------------------------:
![](https://github.com/noseglasses/elf_diff/blob/119a0b62c5d7faf2d0b7a958b46f7daf4ee8bcc7/examples/multi_page_pair_report.png)  |  ![](https://github.com/noseglasses/elf_diff/blob/119a0b62c5d7faf2d0b7a958b46f7daf4ee8bcc7/examples/single_page_pair_report.png)

To allow for convenient exchange and archiving, single page reports may also be generated in [pdf](https://github.com/noseglasses/elf_diff/blob/master/examples/elf_diff_test_static_1.pdf) format.

__Please__ __note__: If you are familiar with _elf_ _files_, the terms _symbol_ and _name_ _mangling_, you know how compilers and linkers transform 
high level language code into binary code and how this code is stored in elf files, you might want to skip the remaining parts of the introduction section.

### Content of Reports

Now, after you had a look at the different types of reports that _elf_diff_ generates, you might be interested in how the contained information is established.

As already mentioned, _elf_diff_ compares binaries based on the contained symbols.

#### Symbols

Symbols resulting from functions and variables like

```cpp
int Test1::f(int a, int b) { return 42; }

double a = 0.3;
``` 

have the following properties:

* a unique name (possibly including a namespace), e.g. `Test1::f`,
* a signature (functions), e.g. `(int a, int b)->int`,
* a symbol type (variable/constant/function and subtle variants of those),
* an extension (the amount of RAM or program memory that the symbol occupies, the latter only when compiled for [harvard architectures](https://en.wikipedia.org/wiki/Harvard_architecture)) and
* associated code/data.

__Please note:__ There are several other properties but those are not important for understanding what _elf_diff_ does.

#### A Brief Excursion About Name Mangling

You might be surprised that the _data_ _type_ of variables is not part of the above list.

This is because the variable data type is actually not stored in elf files. They are simply no more required after
the end of the compile process. At that point all variables have become named addresses of a memory areas of known extension.

It is simply sufficient that the compiled code knows what to do with such addresses and memory extensions.

Next, you might frown and ask why the same argument apparently does not apply to function signatures? Those are very well listed above.
Can't the compiler treat function parameters in the same way as variables?

There are several answers to that question. We will concentrate on the one that is, subjectively, most related to the current topic. The answer is: _function_ _overloading_.

Many high level languages (as e.g. C++) allow functions with idential names but different call signatures 
to be used in the same program, e.g.

```cpp
void f(double)
```
and 
```cpp
void f(int)
```

To avoid name clashes, compilers and linkers use an approach called [name mangling](https://en.wikipedia.org/wiki/Name_mangling) 
to convert names and signatures into so called _mangled_ _symbol_ _names_. 

The mangled names are what is actually stored in the elf files (unless [stripped](https://en.wikipedia.org/wiki/Strip_(Unix)).

Name mangling is, however, a reversible process. Compilers typically come with utilities that allow restoring name and signature from mangled names,
a process commonly called _demangling_ (e.g. by means of the tool [c++filt](https://sourceware.org/binutils/docs/binutils/c_002b_002bfilt.html) that is part of the GNU binutils suite).

We still haven't answered the question how symbols, or rather their properties can be used to find the differences between compiled binaries. So let's get back on track.

#### Comparing Symbols

When comparing two binaries one may group symbols based on their names and signatures (or their mangled names) as

* symbols present in both versions (persisting),
* symbols that are only found in version 2 (new) and
* those that are only present in version 1 (disappeared).

The code snippets initially presented are deliberatly written in a way that eases identifying related pairs of symbols in both versions.

Typically, software is subject to incremental transitions that affect only a quite limited number of symbols.

Symbols might be

* renamed or
* moved to another namespace (which includes being turned from a free function to a class method and vice versa).

Also, their

* signature (functions),
* implementation (functions) or
* data type (variables/constants)

might be changed.

#### Symbol Similarities

_elf_diff_ automatically detects and visualizes pairs of similar symbols. 

Unfortunatelly, in some cases the relations between symbols are not unique.

To help the user finding the most relevant symbol relations, _elf_diff_ displays the level of lexicographic similarity for every pair of similar symbols. 
For functions the level of lexicographic similarity of the two implementations is also displayed.

#### Highlighted Differences

To allow for conveniently analyzing implementation changes at the assembly level, the disassembled code is displayed side-by-side with differences being highlighted.

If debug information is contained in the binaries (flag `-g` of the gcc compiler),
the original high level language code annotates the assembly.

If you want to find out about other applications of _elf_diff_, please keep on reading.

Don't forget to have a look at the examples section at the end of this document.

## Purpose

* resource/performance optimization
* debugging
* learning/teaching

The main purpose of _elf_diff_ is to determine how specific changes to a piece of software affect resource consumption and performance. The tool may also serve to compare two independent change sets or just to have fun and learn how changes reflect in the generated assembly code.

The following information is part of _elf_diff_'s report pages:

* differences in the amount of program storage and static RAM usage
* symbols that are only present in one of the two versions
* symbols whose naming or call signature is similar in both versions, e.g. as a result of symbol renaming or subtly changing call signatures
* assembly code discrepancies of functions with identical names and call signatures

As _elf_diff_ operates on elf-files, it is fairly language and platform agnostic. All it requires to work is a suitable set of [GNU Binutils](https://en.wikipedia.org/wiki/GNU_Binutils) for the target platform.

## Requirements

_elf_diff_ is a Python script. It mostly uses standard libraries but also some non-standard packages (see the file `requirements.txt`) for more information.

_elf_diff_ works and is automatically tested with Python 3.

The following setup guide assumes Python 3 to be installed on your computer. Python setup tutorials can easily be found by googling "install python 3".

## Installing

Install the elf_diff Python package via one of the following commands

* `python3 -m pip install elf_diff` (Linux)
* `py -m pip install elf_diff` (Windows)
	 
__Please note:__ [PyPI](https://pypi.org/) the Python package index traditionally uses hyphens instead of underscores in package names. _pip_, however, happily supports both versions _elf_diff_ and _elf-diff_.

Alternatively when developing _elf_diff_, the following steps are required:

1. Clone the [_elf_diff_](https://github.com/noseglasses/elf_diff) repo from github.
2. Install any required packages via one of the following commands
   * `python3 -m pip install -r requirements.txt` (Linux)
   * `py -m pip install -r requirements.txt` (Windows)
3. Add the `bin` subdirectory of the _elf_diff_ repo to your platform search path (environment variable, e.g. `PATH`)

To run _elf_diff_ from the local git-sandbox, please use the script `bin/elf_diff` that is part of the source code repo, e.g. as `bin/elf_diff -h` to display the help string.

## Usage

There is a small difference between running Python on Linux and Windows. While the command to run Python 3 from a console window under Linux is `python3`, on Windows there is a so called _Python runner_ (command `py`) that invokes the most suitable Python interpreter installed.

To display _elf_diff_'s help page in a console window, type the following in a Linux console
```sh
python3 -m elf_diff -h
```
or
```sh
py -m elf_diff -h
```
in a Windows console.

In the examples provided below, we prefer the Linux syntax. Please replace the keyword `python3` with `py` when running the respective examples in a Windows environment.

### Generating Pair-Reports

To generate a pair report, two binary files need to be passed to _elf_diff_ via the command line. Let's assume those files are named `my_old_binary.elf` and `my_new_binary.elf`. 

The following command will generate a multipage html report in a subdirectory of your current working directory.
```sh
python3 -m elf_diff my_old_binary.elf my_new_binary.elf
```

### Generating Mass-Reports

__Please note:__ Mass reports have been deprecated and are likely removed from further versions of the software.

Mass reports require a driver file (yaml syntax) that specifies a list of binaries to compare pair-wise. 

Let's assume you have two pairs of binaries that reside in a directory `/home/my_user`.
```txt
binary_a_old.elf <-> binary_a_new.elf
binary_b_old.elf <-> binary_b_new.elf
```

A driver file (named `my_elf_diff_driver.yaml`) would then contain the following information:
```yaml
binary_pairs:
    - old_binary: "/home/my_user/binary_a_old.elf"
      new_binary: "/home/my_user/binary_a_new.elf"
      short_name: "A short name"
    - old_binary: "/home/my_user/binary_b_old.elf"
      new_binary: "/home/my_user/binary_b_new.elf"
      short_name: "B short name"
```

The `short_name` parameters are used in the result tables to reference the respective binary pairs.

By using the driver file, we can now run a mass-report as 
```sh
python3 -m elf_diff --mass_report --driver_file my_elf_diff_driver.yaml
```

This will generate a HTML file `elf_diff_mass_report.html` in your current working directory.

### Generating pdf-Files

The generation of pdf reports with _elf_diff_ requires the Python package [weasyprint](https://weasyprint.org). See the [weasyprint installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation) for more information.

__Please note:__ _elf_diff_ generates both types of html reports even without weasyprint being installed.

pdf files are generated by supplying the output file name using the parameter `pdf_file` either at the command line 

```sh
python3 -m elf_diff --pdf_file my_pair_report.pdf my_old_binary.elf my_new_binary.elf
```
or from within a driver file, e.g.
```yaml
pdf_file: "my_pair_report.pdf"
```

### Specifying an Alternative HTML File Location

Similar to specifying an explicit filename for pdf files, the same can be done for our HTML output files, either via the command line
```sh
python3 -m elf_diff --html_file my_pair_report.hmtl my_old_binary.elf my_new_binary.elf
```
or from within a driver file, e.g.
```yaml
html_file: "my_pair_report.html"
```
this will create a single file HTML report (with the exact same content as generated pdf files).

### Specifying an Alternative HTML Directory

To generate a multi-page HTML report use the command line flag `--html_dir` to generate the HTML files e.g. in directory `my_target_dir`.
```sh
python3 -m elf_diff --html_dir my_target_dir my_pair_report.hmtl my_old_binary.elf my_new_binary.elf
```

### Using Driver Files

The driver files that we already met when generating mass-reports can also generally be used to run _elf_diff_. Any parameters that can be passed as command line arguments to _elf_diff_ can also occur in a driver file, e.g.
```sh
python3 -m elf_diff --mass_report --pdf_file my_file.pdf ...
```
In `my_elf_diff_driver.yaml`
```yaml
mass_report: True
pdf_file: my_file.pdf
...
```
### Supplying a Project Title

A project title could e.g. be a short name that summarizes the changes that you applied between the old and the new version of the compared binaries. Supply a title via the parameter `project_title`.

### Adding Background Information

Additional information about the compared binaries can be added to pair-reports. Use the parameters `old_info_file` and `new_info_file` to supply filenames of text files whose content is supposed to be added to the report.

It is also possible to add general information to reports, e.g. about programming language or compiler version or about the build-system. This is supported through the `build_info` parameter which enables supplying a string that is added to the report. For longer strings, this can be conveniently done via the driver-file.

Everything that follows after `build_info: >` in the example will be added to the report.
```yaml
build_info: >
  This build
  info is added to the report.
  The whitespaces in front of these lines are removed, the line breaks are
  preserved.
```

### Using Alias Strings

If you want to obtain anonymized reports, it is not desirable to reveile details about your user name (home directory) or the directory structure. In such a case, the binary filenames can be replaced by alias wherever they would appear in the reports. 

Supply alias names using the `old_alias` and `new_alias` parameters for the old or the new version of the binaries, respectively.

### Working with Cross-Build Binaries

When working on firmware projects for embedded devices, you typically will be using a cross-build environment. If based on GNU gcc, such an environment usually not only ships with the necessary compilers but also with a set of additional tools called [GNU Binutils](https://en.wikipedia.org/wiki/GNU_Binutils).

_elf_diff_ uses some of these tools to inspect binaries, namely `nm`, `objdump` and `size`. Although some information about binaries can be determined even with the host-version of these tools, it is e.g. not possible to retreive disassemblies.

In a cross-build environment, Binutils executable are usually bundled in a specific directory. They also often have a platform-specific prefix, to make them distinguishabel from their host-platform siblings. For the [avr](https://en.wikipedia.org/wiki/AVR_microcontrollers)-version of Binutils e.g., that is shipped with the [Arduino](https://en.wikipedia.org/wiki/Arduino) development suite, the prefix `avr-` is used. The respective commands are, thus, named `avr-nm`, `avr-objdump` and `avr-size`.

To make those dedicated binaries known to _elf_diff_, please add the binutils directory to the PATH environment variable, use the parameters `bin_dir` and `bin_prefix` or explicitly define the 
commands e.g. `objdump_command` (see command help).

A pair-report generation command for the avr-plattform would e.g. read

```sh
python3 -m elf_diff --bin_dir <path_to_avr_binaries> --bin_prefix "avr-" my_old_binary.elf my_new_binary.elf
```
The string `<path_to_avr_binaries>` in the above example would of course be replaced by the actual directory path where the binaries live.

### Generating a Template Driver File

To generate a template driver file that can serve as a basis for your own
driver files, just run _elf_diff_ with the `driver_template_file` parameter, e.g. as
```sh
python3 -m elf_diff --driver_template_file my_template.yaml
```

Template files contain the default values of all available parameters, or - if the temple file is generated in the same session where a report was created - the template file will contain the actual settings used for the report generation.

### Selecting and Excluding Symbols

By means of the command line arguments `symbol_selection_regex` and `symbol_exclusion_regex`, symbols can be explicitly selected and excluded.
The specified regular expressions are applied to both the old and the old binary. For more fine grained selection, please used the `*_old` and `*_new` versions of the 
respective command line arguments.

### Skip Similar Symbols Detection

Similar symbol detection can be a very useful tool but it is a quite costly operation as it requires comparing all symbol names from one binary with all symbols from the other.
Assuming that both binaries contain `n` symbols this is a `O(n^2)` operation. Therefore it is up to the user to disabe similar symbol detection and output via the command
line argument `--skip_symbol_similarities`.

### Assembly Code

For most developers who are used to program in high level languages, assembly code is a mystery.
Still, there is some information that an assembly-novice can gather from observing assembly code. Starting with the number of assembly code statements. Normally less means good. The more assembly statements there are representing a high level language statement, the more time the processor needs to process them. On the contrary, sometimes there may be a suspiciously low number of assembly statements which might indicate that the compiler has optimized away something that it shouldn't have.

All this, of course, relies on the knowledge about what assembly code is associated with which line of source.
This information is not included in compiled binaries by default. The compiler must explicitly be told to export additional debugging information. For the gcc-compiler the flag `-g`, e.g., will cause this information to be emitted. But careful, some build systems when building debug versions replace optimization flags like `-O3` with the debug flag `-g`. This is not what you want when looking at the performance of your code. Instead you want to add the `-g` flag and keep the optimization flag(s) in place. CMake, e.g. has a configuration variable `CMAKE_BUILD_TYPE` that can be set to the value `RelWithDebInfo` to enable a release build (with optimization enabled) that also comes with debug symbols.

For binaries with debug symbols included, elf_diff will annotate the assembly code by adding the high level language statements that it was generated from.

### Dwarf Debug Info

If compiled with appropriate compiler flags (e.g. gcc's `-g`) generated binaries contain debug information in Dwarf-format that can be extracted
by using GNU binutils. If present, this debug information enables `elf_diff` to e.g. determine the location of definition of symbols in the
source code (file, line, column).

### Migrated Symbols

Debugging information available in elf files' Dwarf debug sections can be used to identify migrated symbols, i.e. those symbols that have been moved from one source file to another.

A symbol is identified as _migrated_ if it is a persisting symbol and if it's source file changed when comparing old and new binary.
If both binaries where compiled from different source trees, all persisting symbols will be identified as migrated. This is because
_elf_diff_ does a lexicographic comparison of source file paths.
In that case the configuration parameters _source_prefix_, _old_source_prefix_ or _new_source_prefix_ may be used to eliminate erroneously identified migratred symbols. This works by stripping path prefix from source file paths.

Example:

A symbol with new and old source files `/dir1/some/source_file.cpp` and `/dir2/some/source_file.cpp` is identified as migrated unless
the path prefix `/dir1/` and `/dir2/` are stripped off.

### Document Structure and Plugin System

When analyzing elf binaries and processing output, _elf_diff_ relies on a intermediate datastructure that it establishes after all symbols have been parsed
from the elf files. This data structure, called _elf_diff_ document, is the basis for the actual file export.

File export relies on dedicated data export plugins for (html, pdf, yaml, json, txt, ...). Plugins receive the _elf_diff_ document and can easily extract
and process its data to generate output of arbitrary type.

### User Defined Plugins

_elf_diff_'s plugin system enables developing user plugins, e.g. for custom output based on the _elf_diff_ document.
Custom plugins are registered via the command line flag `--load_plugin`, specifying the plugin's Python module path and the name of the plugin class
that is supposed to be loaded. Optionally the loaded plugin object can be parametrized by supplying parameter name value pairs.

The following example demonstrates how to load a plugin class `MyPluginClass` from a used defined module `my_plugin_module.py`.

```sh
python3 -m elf_diff --load_plugin "~/some/dir/my_plugin_module.py;MyPluginClass;my_arg1=42;my_arg2=bla" libfoo_old.a libfoo_new.a
```

This example of course assumes that the user plugin knows how to interpret the two parameters `my_arg1` and `my_arg2`.

Plugin classes must be derived from one of the plugin classes defined in elf_diff's module `plugin.py`. Please see elf_diff's default plugins
in the subdirectories of `<elf_diff_sandbox>/src/elf_diff/plugins` as a reference on how to implement custom plugins.

## Running the Tests

_elf_diff_ comes with a number of tests in the `tests` subdirectory of its git repository.
Some tests are unit tests others integration tests that run _elf_diff_ through
its CLI by supplying different command line parameter sets.

To run the entire test bench do the following.

```sh
cd <repo root>
python3 ./tests/test_main.py
```

### Running Individual Test Cases

Test cases reside in the directory `tests/test_cases` of _elf_diff_'s git repository.

To run individual tests, run the test driver and submit one or more tests using the command line arguments `-t`. To run e.g. the test case `test_command_line_args`, do as follows:

```sh
cd <repo root>
python3 ./tests/test_main.py -t test_command_line_args
```

## Examples

### Examples Page

See the [examples page](https://noseglasses.github.io/elf_diff/).

### libstdc++

[Comparison of two versions of libstdc++](https://github.com/noseglasses/elf_diff/blob/master/examples/libstdc++_std_string_diff.pdf) shipping with gcc 4.8 and 5. There are vast differences between those two library versions which result in a great number of symbols being reported. The following command demonstrates how report generation can be resticted to a subset of symbols by using regular expressions.
In the example we select only those symbols related to class `std::string`.

```sh
## Generated on Ubuntu 20.04 LTS
python3 -m elf_diff \
   --symbol_selection_regex "^std::string::.*"   # select any symbol name starting with std::string:: \
   --pdf_file libstdc++_std_string_diff.pdf      # generate a pdf file \
   /usr/lib/gcc/x86_64-linux-gnu/4.8/libstdc++.a # path to old binary \
   /usr/lib/gcc/x86_64-linux-gnu/5/libstdc++.a   # path to new binary
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process
for submitting pull requests to us.

## Versioning

We use [SemVer](https://semver.org/) for versioning. For the versions available,
see the tags on this repository.

## Authors

* noseglasses - Initial work

## License

This project is licensed under the GNU General Public License Version 3
see the LICENSE.md file for details
