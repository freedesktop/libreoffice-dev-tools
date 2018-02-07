.PHONY : coverage

CLANGDEFS=-D__STDC_CONSTANT_MACROS -D__STDC_FORMAT_MACROS -D__STDC_LIMIT_MACROS -fno-rtti
CLANGWARNS=-Werror -Wall -Wno-missing-braces -Wnon-virtual-dtor -Wendif-labels -Wextra -Wundef -Wunused-macros -Wshadow -Woverloaded-virtual
CLANGFLAGS = $(CLANGDEFS) $(CLANGWARNS) -g -std=c++11
CLANGLIBS = -lclangAST -lclangBasic -lclangFrontend -lclangRewrite -lclangTooling -lLLVMSupport
ifneq ($(GCOV),)
CLANGFLAGS += --coverage
endif

all: bin/rename bin/find-unprefixed-members bin/find-harmful-auto

bin/rename: rename.cxx Makefile
	clang++ $(CLANGFLAGS) $(CLANGLIBS) -ldl -lpthread -o $@ $<

bin/find-unprefixed-members: find-unprefixed-members.cxx Makefile
	clang++ $(CLANGFLAGS) $(CLANGLIBS) -ldl -lpthread -o $@ $<

bin/find-harmful-auto: find-harmful-auto.cxx Makefile
	clang++ $(CLANGFLAGS) $(CLANGLIBS) -ldl -lpthread -o $@ $<

test: test.cxx test.hxx Makefile
	clang++ -o test test.cxx

check: bin/rename
	qa/test-rename.sh

coverage:
	rm -f bin/rename rename.cxx.gc{da,no}
	$(MAKE) GCOV=y bin/rename
	$(MAKE) check
	lcov --directory $(PWD) --gcov-tool $(PWD)/qa/llvm-gcov.sh --capture --output-file clang.info
	genhtml -o coverage clang.info
	@echo "Now open <file://$(PWD)/coverage$(PWD)/rename.cxx.gcov.html>"

# vim: set noet sw=4 ts=4:
