## Notes
# This file and any included file here can be included in any other project. It will always make the same files.
# It will warn if it is built recursively rather than included, but it should still make the same.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

## How to reach here from the current working directory
_Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(_Makefile)))))

# $/ is now the path prefix needed to reach here from `cwd`.
# It looks similar to `~/` on purpose, but it expands to nothing if already here.

## How to make a generic project (and its subprojects, if they have at least an .md file)
# `make`: All executables from all source code is executable.
# `make build/*.py.bringup`: *.py is executable with the venv/bin/python3 next to it.
# `make build/$(dir $(realpath .)).bringup`: A _start or main() found in *.c *.cpp *.s is executable.
# `make build/*.tested`: Executable * is verified.
# `make report`: Print a project self-test summary.
# `make gfm pdf html slides`: Print reports with all details of the project.
# `make old changes review audit`: Compare the project with last release.
# clean: Remove everything built by the project.
$(info -include $/project.mk)
-include $/project.mk

## How to make that generic project maker
ifneq (clean,$(findstring clean,$(MAKECMDGOALS)))
    $/project.mk: $/generic.mk $/makemake.py
	    mkdir -p $(dir $@) && cat $< | \
	      sed 's/{" ".join(sys.argv)}/$(MAKE) $(MAKECMDGOALS)/g' | \
	      sed 's/{_}/$(notdir $(realpath $(dir $@)))/g' | \
	      sed 's|{build_dir}|build/|g' | \
	      sed 's/{makemake_py}/makemake.py/g' > $@
    $/generic.mk $/makemake.py:
	    curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/$(notdir $@) -o $@
    .PRECIOUS: $/makemake.py
endif

## How to clean also that
$/clean: $/clean_project
$/clean_project:
	rm -f $/project.mk

## How to find subdirectories containing at least one .md file
$/SUBDIRS := $(foreach d,$(shell find $/. -mindepth 1 -maxdepth 1),$(notdir $d))
$/SUBPROJECTS := $(sort $(dir $(foreach d,$($/SUBDIRS),$(wildcard $/$d/*.md))))
$/ACTIVE_SUBPROJECTS := $(dir $(foreach d,$($/SUBPROJECTS),$(wildcard $/$d/Makefile)))

## How to make these as sub-projects before this project
$/all: | $($/ACTIVE_SUBPROJECTS:%=%all)
$/tested: | $($/ACTIVE_SUBPROJECTS:%=%tested)
$/build/report.txt: $($/ACTIVE_SUBPROJECTS:%=%build/report.txt)
$/gfm: | $($/ACTIVE_SUBPROJECTS:%=%gfm)
$/pdf: | $($/ACTIVE_SUBPROJECTS:%=%pdf)
$/html: | $($/ACTIVE_SUBPROJECTS:%=%html)
$/slides: | $($/ACTIVE_SUBPROJECTS:%=%slides)
$/old: | $($/ACTIVE_SUBPROJECTS:%=%old)
$/new: $($/ACTIVE_SUBPROJECTS:%=%new)
$/build/review.diff: $($/ACTIVE_SUBPROJECTS:%=%build/review.diff)
$/clean: | $($/ACTIVE_SUBPROJECTS:%=%clean)

## Finally attempt to include all sub-projects
# Note: Subprojects modify $/, this has to be the last command using it as a prefix to here.
$(info -include $($/SUBPROJECTS:%=%Makefile))
-include $($/SUBPROJECTS:%=%Makefile)