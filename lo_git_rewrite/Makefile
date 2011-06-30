
OS=$(shell uname)

ifeq ($(OS), Darwin)
COPT=
else
COPT="-march=native"
endif

all: lo_git_rewrite

clean:
	rm -f lo_git_rewrite

clean_spaces: lo_git_rewrite.c
	gcc -O2 $(COPT) log_git_rewrite.c -o lo_git_rewrite


