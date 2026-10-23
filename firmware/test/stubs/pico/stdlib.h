// Minimal host stand-ins for the Pico SDK, enough to compile rover_move.hpp.
#pragma once
#include <cstdint>
#include <deque>

typedef unsigned int uint;
typedef uint64_t absolute_time_t;

namespace host {
inline uint32_t now_ms = 0;
inline std::deque<char> uart_rx;
inline int pwm_level[32] = {};
inline int dir[32] = {};
}

inline absolute_time_t get_absolute_time() { return host::now_ms; }
inline uint32_t to_ms_since_boot(absolute_time_t t) { return (uint32_t)t; }
inline void sleep_ms(uint32_t ms) { host::now_ms += ms; }

#define GPIO_OUT 1
#define GPIO_FUNC_PWM 4
#define GPIO_FUNC_UART 2
inline void gpio_init(uint) {}
inline void gpio_set_dir(uint, bool) {}
inline void gpio_set_function(uint, int) {}
inline void gpio_put(uint pin, bool v) { host::dir[pin] = v; }
