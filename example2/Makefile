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
_example2_abspath := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_example2 := $(subst $(PWD)/,,$(_example2_abspath))
ifneq ($(strip $(_example2)),)
  _inside_example2 := ( cd $(_example2) && #
  _outside_example2 := ) #
endif

# If we do want to build stuff:
ifeq ($(filter $(_example2)clean clean,$(MAKECMDGOALS)),)
  -include $(_example2)build.mk
endif

# python3 on Linux, or python.exe on Windows
PYTHON ?= python3

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
$(_example2)all: $(_example2)build.mk
$(_example2)build.mk: $(_example2)makemake.py
	$(_inside_example2)$(PYTHON) makemake.py --makemake --generic $(_outside_example2)> $@
$(_example2)makemake.py: $(_example2)../makemake.py
	cp $< $@

# Remove built stuff here.
$(_example2)clean:
	rm -rf $(_example2)build/ $(_example2)venv/ $(_example2).ruff_cache/
	rm -f $(_example2)makemake.py $(_example2)build.mk
	rm -f $(_example2)example2 $(_example2)*.pdf $(_example2)*.html $(_example2)*.gfm

# Compilation steps are still under development, so this rule applies here.
$(_example2_DEPS) $(_example2_OBJS): $(_example2)Makefile $(_example2)build.mk
