#pragma once
#define uart0 0
inline void uart_init(int, uint) {}
inline bool uart_is_readable(int) { return !host::uart_rx.empty(); }
inline char uart_getc(int) { char c = host::uart_rx.front(); host::uart_rx.pop_front(); return c; }
