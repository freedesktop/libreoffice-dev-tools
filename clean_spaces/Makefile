
OS=$(shell uname)

ifeq ($(OS), Darwin)
COPT=
else
COPT="-march=native"
endif

all: clean_spaces

clean_spaces: clean_spaces.c
	gcc -O2 $(COPT) -pthread clean_spaces.c -o clean_spaces


