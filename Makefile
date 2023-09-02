# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
all: build.mk
build.mk: makemake.py
	python3 -m makemake --makemake --generic > $@

# If we do want to build stuff, include its builder:
ifeq ($(filter clean,$(MAKECMDGOALS)),)
  -include build.mk
endif

# Manage the example sub-project also.
include example/Makefile
all: | example/all
tested: | example/tested
report: | example/report
gfm: | example/gfm
pdf: | example/pdf
html: | example/html
slides: | example/slides
old: | example/old
new: gfm
project_changes: | example/project_changes
clean: | example/clean
	rm -rf venv/ build/ .ruff_cache/
	rm -f build.mk makemake.dep *.pdf *.html *.gfm

# Compilation steps are still under development, so this rule applies here.
$(_normalize_DEPS) $(_normalize_OBJS): Makefile build.mk
