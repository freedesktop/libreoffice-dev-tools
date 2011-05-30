
OS=$(shell uname)

ifeq ($(OS), Darwin)
COPT=
else
COPT="-march=native"
endif

all: clean_spaces clean_spaces_mp

clean_spaces: clean_spaces.c
	gcc -O2 $(COPT) clean_spaces.c -o clean_spaces

clean_spaces_mp: clean_spaces_mp.c
	gcc -O2 $(COPT) -pthread clean_spaces_mp.c -o clean_spaces_mp

