# all (default): Install everything.
# venv: Install a python environment.
# tested: Test everything.
# report: Print a test summary.
# gfm pdf html slides: Print a project report.
# old changes review audit: Compare with last release.
# clean: Remove everything built here.

# Do not risk using any broken stuff!
.DELETE_ON_ERROR:

# Figure out how to reach here from the current working directory.
_example_abspath := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_example := $(subst $(PWD)/,,$(_example_abspath))
ifneq ($(strip $(_example)),)
  _inside_example := ( cd $(_example) && #
  _outside_example := ) #
endif

# If we do want to build stuff: include a generic builder
ifeq ($(filter $(_example)clean clean,$(MAKECMDGOALS)),)
  -include $(_example)build.mk
endif

# python3 on Linux, or python.exe on Windows
PYTHON ?= python3

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
$(_example)all: $(_example)build.mk
$(_example)build.mk: $(_example)makemake.py
	$(_inside_example)$(PYTHON) makemake.py --makemake --generic $(_outside_example)> $@
$(_example)makemake.py: $(_example)../makemake.py
	cp $< $@

# Remove built stuff here.
$(_example)clean:
	rm -rf $(_example)build/ $(_example)venv/ $(_example).ruff_cache/
	rm -f $(_example)makemake.py $(_example)build.mk
	rm -f $(_example)example $(_example)*.pdf $(_example)*.html $(_example)*.gfm

# Compilation steps are still under development, so this rule applies here.
$(_example_DEPS) $(_example_OBJS): $(_example)Makefile $(_example)build.mk
