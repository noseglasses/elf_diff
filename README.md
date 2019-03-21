# elf_diff - A Tool to compare elf binaries

## Usage

```
elf_diff 
   <--old old_binary_file> 
   <--new binary_file>
   [--bin-dir binary_directory]
   [--bin-prefix binary_prefix]
```

* old_binary_file: The first input elf binary (considered to be the old state)
* new_binary_file: The second input elf binary (considered to be the new state)
* binary_directory: A directory where binutils executables can be found (defaults to `/usr/bin`)
* binary_prefix: A prefix that is added to all binutils executables (e.g. `avr-`) 
