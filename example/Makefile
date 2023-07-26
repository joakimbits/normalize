# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.
_example_abspath := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_example := $(subst $(PWD)/,,$(_example_abspath))
ALL += $(_example)build.mk

.DELETE_ON_ERROR:
all: $(ALL)
$(_example)build.mk:
	python3 $(_example)../makemake.py --makemake --generic > $@
clean:
	rm -rf build/
	rm -f build.mk example

-include $(_example)build.mk