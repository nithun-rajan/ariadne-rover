CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Werror

test: test_rover_move
	./test_rover_move

test_rover_move: test_rover_move.cpp ../src/rover_move.hpp
	$(CXX) $(CXXFLAGS) -Istubs -o $@ test_rover_move.cpp

clean:
	rm -f test_rover_move

.PHONY: test clean
