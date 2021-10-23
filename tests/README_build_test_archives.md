# Howto Build Test Archives

To build test archives do the following on a Ubuntu Linux system.

## x86_64
```sh
cd <repo_root>/tests
cmake .
make
```

## arm
```sh
cd <repo_root>/tests
cmake . -DCMAKE_TOOLCHAIN_FILE=./toolchain_gcc-arm-linux-gnueabi.cmake -DPLATFORM=arm
```
