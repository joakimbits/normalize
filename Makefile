## Generic make targets
# all: Bringup all (default)
# build/%.bringup: Bringup one.
# report: Print a self-test summary.
# gfm pdf html slides: Print a self-test project report.
# old changes review audit: Compare all sources with last release.
# clean: Remove everything built here.

## Notes
# This file and any included file here can be included in any other project. It will always make the same files.
# It will warn if it is built recursively rather than included, but it should still make the same.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Reach here from the current working directory
_Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(_Makefile)))))

# `$/` is now the path prefix needed to reach here from `cwd`.
# It looks similar to `~/` on purpose, but it expands to nothing if already here.

# Make the main project maker before we know which PYTHON to use
$/project.mk: $/generic.mk $/makemake.py
	mkdir -p $(dir $@) && cat $< | \
	  sed 's/{" ".join(sys.argv)}/$(MAKE) $(MAKECMDGOALS)/g' | \
	  sed 's/{_}/$(notdir $(realpath $(dir $@)))/g' | \
	  sed 's|{build_dir}|build/|g' | \
	  sed 's/{makemake_py}/makemake.py/g' > $@

# Include our main project and use its PYTHON to make a subproject maker
-include $/project.mk
ifdef PYTHON
    $/%/Makefile: $/makemake.py $/generic.mk | $/project.mk
	    $(PYTHON) $< --makemake --generic > $@
	    cp $^ $(dir $@)
endif

# List all its sub-projects
$/_SUB_PROJECTS := $/example $/example2

# Build the sub-projects automatically
$/all: | $($/_SUB_PROJECTS:%=%/all)
$/tested: | $($/_SUB_PROJECTS:%=%/tested)
$/build/report.txt: $($/_SUB_PROJECTS:%=%/build/report.txt)
$/gfm: | $($/_SUB_PROJECTS:%=%/gfm)
$/pdf: | $($/_SUB_PROJECTS:%=%/pdf)
$/html: | $($/_SUB_PROJECTS:%=%/html)
$/slides: | $($/_SUB_PROJECTS:%=%/slides)
$/old: | $($/_SUB_PROJECTS:%=%/old)
$/new: $($/_SUB_PROJECTS:%=%/new)
$/build/review.diff: $($/_SUB_PROJECTS:%=%/build/review.diff)
$/clean: | $($/_SUB_PROJECTS:%=%/clean)
	rm -f $/project.mk $($/_SUB_PROJECTS:%=%/Makefile)

# Finally include all subprojects. Since they change $/, we cannot use our $/ after that.
-include $($/_SUB_PROJECTS:%=%/Makefile)