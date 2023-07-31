# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Define an initial default build target $(_example)all: A definition of how to build stuff here.
all: build.mk
build.mk:
	python3 -m makemake --makemake --generic > $@

# Report test results: First those of an example sub-project (by a target after |) and then those here.
report: build/makemake.py.tested | example/report
	@$(foreach tested,$^,echo "___ $(tested): ____" && cat $(tested) ; )

# Remove built stuff: First those of an example sub-project (by a target after :) and then those here.
clean: example/clean
	rm -rf venv/ build/
	rm -f build.mk style syntax makemake.dep

# If we do want to build stuff:
ifeq ($(filter clean,$(MAKECMDGOALS)),)
  # Redefine the default build target "all" to build stuff from source files found here.
  -include build.mk
endif

# Include an example include-from-anywhere sub-project.
-include example/Makefile
