# Generic tester for source files next to this Makefile
# Will compile any .cpp, .c and .s files and integrate them into a single executable named as the parent folder.
# Will bringup a local venv for any .py files and test all python and command line examples found in them.
_dir_abspath := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
_dir := $(subst $(PWD)/,,$(_dir_abspath))
_dir_build := $(subst $(PWD)/,,$(_dir_abspath)build/)

.DELETE_ON_ERROR:
all: $(_dir)build.mk
$(_dir)build.mk:
	python3 makemake.py --makemake --generic > $@
test_example_project:
	( cd example && make clean --no-print-directory && \
	  make --no-print-directory && cat build/example.tested )
clean:
	rm -rf venv/ build/
	rm -f build.mk style syntax makemake.dep

-include $(_dir)build.mk

report: $(_dir)build.mk $(_dir_build)makemake.py.tested $(_dir)example/build/example.tested
	cat $(_dir)build.mk  ##########################
	ls $(_dir_build)  #############################
	cat $(_dir_build)makemake.py.d  ###############
	cat $(_dir_build)makemake.py.bringup  #########
	cat $(_dir_build)makemake.py.tested  ##########
	cat $(_dir)example/build/example.tested  ######
