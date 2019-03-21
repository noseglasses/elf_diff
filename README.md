# elf_diff - A Tool to compare elf binaries

## Usage

```
elf_diff 
   <--old old_binary_file> 
   <--new binary_file>
   [--bin-dir binary_directory]
   [--bin-prefix binary_prefix]
   [--text-file text_output_file]
   [--html-file html_output_file]
```

* old_binary_file: The first input elf binary (considered to be the old state)
* new_binary_file: The second input elf binary (considered to be the new state)
* binary_directory: A directory where binutils executables can be found (defaults to `/usr/bin`)
* binary_prefix: A prefix that is added to all binutils executables (e.g. `avr-`) 
* text_file: If defined, text output is redirected to this file
* html_file: If defined, only html is generated and written to this file

## Requirements

The following Python packages are required to run elf_diff:

* argparse
* difflib
* re
* jinja2, inspect (only if html output is requested)
