# Example include-from-anywhere project builder
#
# Each target gets a prefix which is the path to here from the current working director .
#
# Targets defined:
#   all: Use makemake to build everything below except makemake.py and clean.
#   makemake.py: Install ../makemake.py here.
#   example: Compile any .cpp, .c and .s files into this executable named as its parent folder.
#   venv: Bringup a local python environment here.
#   build/%.mk: Build installation recipy here.
#   build/%.bringup: Install and report output here.
#   build/%.tested: Test and report output here.
#   report: Test everything that still needs testing, and print a test summary if all tests are OK.
#   pdf: Build a software project report here.
#   clean: Remove everything built here.


# Figure out how to reach here from the current working directory.
_example_abspath := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_example := $(subst $(PWD)/,,$(_example_abspath))
ifneq ($(strip $(_example)),)
  _inside_example := ( cd $(_example) && #
  _outside_example := ) #
endif

# Do not risk using any broken stuff!
.DELETE_ON_ERROR:

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
$(_example)all: $(_example)build.mk
$(_example)build.mk: $(_example)../makemake.py | $(_example)makemake.py
	$(_inside_example)python3 -m makemake --makemake --generic $(_outside_example)> $@
$(_example)makemake.py:
	$(_inside_example)ln -sf ../makemake.py makemake.py $(_outside_example)

# Remove built stuff here.
$(_example)clean:
	rm -rf $(_example)build/ $(_example)venv/ $(_example).ruff_cache/
	rm -f $(_example)makemake.py $(_example)build.mk
	rm -f $(_example)example $(_example)*.pdf

# If we do want to build stuff:
ifeq ($(filter $(_example)clean clean,$(MAKECMDGOALS)),)
  # Redefine the default build target $(_example)all to build stuff from source files here.
  -include $(_example)build.mk
endif

# Compilation steps are still under development, so this rule applies here.
$(_example_DEPS) $(_example_OBJS): $(_example)Makefile $(_example)build.mk
