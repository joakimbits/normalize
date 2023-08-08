# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
all: build.mk
build.mk: makemake.py
	python3 -m makemake --makemake --generic > $@

# Report example also.
report: | example/report

# Remove built stuff.
clean: example/clean
	rm -rf venv/ build/ .ruff_cache/
	rm -f build.mk makemake.dep *.pdf

# If we do want to build stuff:
ifeq ($(filter clean,$(MAKECMDGOALS)),)
  # Redefine the default build target "all" to build stuff from source files found here.
  -include build.mk
endif

# Include example sub-project.
-include example/Makefile

# Compilation steps are still under development, so this rule applies here.
$(_normalize_DEPS) $(_normalize_OBJS): Makefile build.mk
