set(CMAKE_SYSTEM_NAME               Generic)
set(CMAKE_SYSTEM_PROCESSOR          arm)

# Without that flag CMake is not able to pass test compilation check
set(CMAKE_TRY_COMPILE_TARGET_TYPE   STATIC_LIBRARY)

set(BAREMETAL_ARM_TOOLCHAIN_PATH "/usr/bin/")

set(CMAKE_AR                        ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-ar${CMAKE_EXECUTABLE_SUFFIX})
set(CMAKE_ASM_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-gcc${CMAKE_EXECUTABLE_SUFFIX})
set(CMAKE_C_COMPILER                ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-gcc${CMAKE_EXECUTABLE_SUFFIX})
set(CMAKE_CXX_COMPILER              ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-g++${CMAKE_EXECUTABLE_SUFFIX})
set(CMAKE_LINKER                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-ld${CMAKE_EXECUTABLE_SUFFIX})
set(CMAKE_OBJCOPY                   ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-objcopy${CMAKE_EXECUTABLE_SUFFIX} CACHE INTERNAL "")
set(CMAKE_RANLIB                    ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-ranlib${CMAKE_EXECUTABLE_SUFFIX} CACHE INTERNAL "")
set(CMAKE_SIZE                      ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-size${CMAKE_EXECUTABLE_SUFFIX} CACHE INTERNAL "")
set(CMAKE_STRIP                     ${BAREMETAL_ARM_TOOLCHAIN_PATH}arm-linux-gnueabi-strip${CMAKE_EXECUTABLE_SUFFIX} CACHE INTERNAL "")

set(CMAKE_C_FLAGS                   "-Wno-psabi -fdata-sections -ffunction-sections -Wl,--gc-sections" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS                 "${CMAKE_C_FLAGS} -fno-exceptions" CACHE INTERNAL "")

set(CMAKE_C_FLAGS_DEBUG             "-Os -g" CACHE INTERNAL "")
set(CMAKE_C_FLAGS_RELEASE           "-Os -DNDEBUG" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_DEBUG           "${CMAKE_C_FLAGS_DEBUG}" CACHE INTERNAL "")
set(CMAKE_CXX_FLAGS_RELEASE         "${CMAKE_C_FLAGS_RELEASE}" CACHE INTERNAL "")

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
