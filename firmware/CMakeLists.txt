cmake_minimum_required(VERSION 3.13)

# Point PICO_SDK_PATH at a pico-sdk checkout, in the environment or with
#   cmake -DPICO_SDK_PATH=/path/to/pico-sdk ..
if(NOT PICO_SDK_PATH)
    set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
endif()
if(NOT PICO_SDK_PATH)
    message(FATAL_ERROR "Set PICO_SDK_PATH to your pico-sdk checkout")
endif()
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)

set(PICO_BOARD pico CACHE STRING "Board type")

project(ariadne_motor C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(rover_move src/main.cpp)

target_link_libraries(rover_move
    pico_stdlib
    hardware_clocks
    hardware_gpio
    hardware_pwm
    hardware_uart
)

pico_add_extra_outputs(rover_move)   # rover_move.uf2 for drag-and-drop flashing
