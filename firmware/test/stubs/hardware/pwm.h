#pragma once
inline uint pwm_gpio_to_slice_num(uint pin) { return pin / 2; }
inline void pwm_set_wrap(uint, uint16_t) {}
inline void pwm_set_enabled(uint, bool) {}
inline void pwm_set_gpio_level(uint pin, uint16_t level) { host::pwm_level[pin] = level; }
