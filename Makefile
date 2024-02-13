# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
all: build.mk
build.mk: makemake.py
	$(PYTHON) -m makemake --makemake --generic > $@

# If we do want to build stuff, include its builder:
ifeq ($(filter clean,$(MAKECMDGOALS)),)
  -include build.mk
endif

# python3 on Linux, or python.exe on Windows
PYTHON ?= python3

# Manage the example sub-projects also.
include example/Makefile example2/Makefile
all: | example/all example2/all
tested: | example/tested example2/tested
build/report.txt: $(_example_TESTED) $(_example2_TESTED)
gfm: | example/gfm example2/gfm
pdf: | example/pdf example2/pdf
html: | example/html example2/html
slides: | example/slides example2/slides
old: | example/old example2/old
new: gfm
build/review.diff: example/build/review.diff example2/build/review.diff
clean: | example/clean example2/clean
	rm -rf build.mk venv/ build/ .ruff_cache/
	rm -f *.pdf *.html *.gfm

# Compilation steps are still under development, so this rule applies here.
$(_normalize_DEPS) $(_normalize_OBJS): Makefile build.mk
