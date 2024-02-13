#!./venv/bin/python3
"""Print a Makefile for handling a python module and exit

Adds the following command line options to the main module:

--makemake: Print a Makefile for bringup and test of the parent module.
--generic: Generalize it so that any other Makefile can include the Makefile.
--dep <file>: Create a separate Makefile for a bringup.

Makes it easy to add the following command line options to the parent module:

--timeout: Time in seconds before giving up on a command-line test.
--sh-test <file>: Test command line usage examples in a file and exit.
--test: Verify python and command line usage examples in the module and exit.
-c <string>: Execute a program string in the module and exit.
--prompt <file> <openai model> <T> <rot13-encoded key>: Print a continuation and exit.


USER MANUAL

To integrate a tool.py module that uses makemake, check the Dependencies section in its
header. Dependencies can include pip installation lines as well as bash commands.

To self-test a tool.py that uses makemake - while adding its dependencies into python3:
$ python3 tool.py --makemake > tool.mk && make -f tool.mk

To self-test all such tools in a folder - while adding their dependencies into venv:
$ python3 tool.py --makemake --generic > Makefile
$ make
<modify any .py in the same folder>
$ make

To use a tools/tool.py in another Makefile:

Makefile:
    tooled.txt: tools/tool.py tools/build/tool.py.bringup | tools/Makefile  # (1, 4)
        tools/venv/bin/python $< > $@  # (5)
    tools/Makefile:
        python3 tools/tool.py --makemake --generic >$@  # (2)
    -include tools/Makefile  # (0, 3)

$ make tooled.txt

How it works:
    0. Make tries to include tools/Makefile but continues without it. (The - continues.)
    1. Make wants tooled.txt, needs tools/build/tool.py.bringup, but can't build it.
    2. Make also needs tools/Makefile and builds that. (The | ignores its timestamp.)
    3. Make detects a tools/Makefile to include and therefore restarts.
    4. Make wants tooled.txt, needs tools/build/tool.py.bringup that needs tools/venv.
       Make builds tools/venv and then tools/build/tool.py.bringup using it. (The
       Dependencies for tools/tool.py gets added to tools/venv and possibly elsewhere).
    5. Make builds tooled.txt using tools/tool.py and that same tools/venv.
       (The $< becomes tools/tool.py, and the $@ becomes tooled.txt).

Usage:
    import makemake  # before importing (other) external dependencies

    if __name__ == '__main__':
        import argparse

        argparser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=makemake.brief(),
            epilog='''Examples:
    $ echo hello world''')

        makemake.add_arguments(argparser)
        args = argparser.parse_args()

Dependencies:
$ python3 -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version'
requests  # Needed for the --prompt option
"""

import sys
import os
import re
from argparse import Action
import pydoc

parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
_ = os.path.split(os.getcwd())[1]
module_path = sys.argv[0]
module_dir, module_py = os.path.split(module_path)
if module_dir:
    path = f"./{module_dir}/"
else:
    path = './'
module, ext = os.path.splitext(module_py)

REVIEW = """
This prompt requires gpt-4 but we prototype it here gpt-3.5

I want you to act as a software developer with the task to release software that
I will describe to you below. Take a look at what I have inspected already
after the (first) --- below. There I used the command `$ make review` which prints 
the last released version number, the commit comments and the changes since then.  

The project report we look at changes within is organized like this:

1.  It explains the project purpose with example usage. 

2.  It has separate sections for listing each source code, installing python code, 
    test results for each source code, and finally test results for the complete 
    integrated project.

You have now four goals:

1. Summarize the commit comments and project changes below in a more user-friendly style as release summary.
2. Choose a title explaining the gits of the changes as release title.   
3. Choose a new semantic version number for the changes as new version. 
4. Fill in the command `git tag -m "<new version> <release title>" <new version>`

---
"""

MAKEFILE_FROM_BUILD_DIR = f"""# $ {" ".join(sys.argv)}
ifeq ($(_{_}_DIR),) 

# A large-context openai model suitable for code review
_{_}_MODEL := gpt-3.5-turbo-16k

# A temperature for the openai continuation.
_{_}_TEMPERATURE = 0.7

# A rot13 encoded openai Bearer key
_{_}_BEARER_rot13 := fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj

# Figure out where to find and build files
_{_}_THIS_MAKEFILE_ABSPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_{_}_ABSPATH := $(dir $(_{_}_THIS_MAKEFILE_ABSPATH))
_{_} := $(subst $(PWD)/,,$(_{_}_ABSPATH))
__{_}_BUILD := %s
_{_}_BUILD := $(subst $(PWD)/,,$(_{_}_ABSPATH)$(__{_}_BUILD))
ifeq ($(_{_}),)
  _{_}_DIR := ./
else
  _{_}_DIR := $(_{_})
endif

# Find all source files
_{_}_SOURCE :=
_{_}_MAKEFILE := $(wildcard $(_{_})Makefile)
_{_}_SOURCE += $(_{_}_MAKEFILE)
_{_}_S := $(wildcard $(_{_})*.s)
_{_}_SOURCE += $(_{_}_S)
_{_}_C := $(wildcard $(_{_})*.c)
_{_}_SOURCE += $(_{_}_C)
_{_}_H := $(wildcard $(_{_})*.h)
_{_}_SOURCE += $(_{_}_H)
_{_}_CPP := $(wildcard $(_{_})*.cpp)
_{_}_SOURCE += $(_{_}_CPP)
_{_}_HPP := $(wildcard $(_{_})*.hpp)
_{_}_SOURCE += $(_{_}_HPP)
_{_}_PY := $(shell cd $(_{_}_DIR) && find . -maxdepth 1 -type f -name '*.py')
_{_}_PY := $(subst ./,$(_{_}),$(_{_}_PY))
_{_}_SOURCE += $(_{_}_PY)
_{_}_MD := $(wildcard $(_{_})*.md)
_{_}_SOURCE += $(_{_}_MD)

# Find our git status
_{_}_BRANCH := $(shell git branch --show-current)
_{_}_BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
_{_}_KNOWN := $(addprefix $(_{_}),$(shell cd $(_{_}_DIR) &&\
 git ls-files . ':!:*/*'))
_{_}_ADD := $(filter-out $(_{_}_KNOWN),$(_{_}_SOURCE))
_{_}_MODIFIED := $(shell cd $(_{_}_DIR) && echo `git status -s . | grep '^ M ' |\
 awk '{{ print $(_{_})$$2 }}'`)
_{_}_REMOVE := $(filter-out $(_{_}_SOURCE),$(_{_}_KNOWN))

# Figure out where to checkout an old worktree
_{_}_HOME_DIR := $(dir $(shell git rev-parse --git-common-_))
_{_}_HOME := $(_{_}_HOME_DIR:./%%=%%)
_{_}_NAME := $(notdir $(abspath $(_{_}_HOME_DIR)))

# ToDo: Refactor _{_}_HERE_DIR into a dynamic variable
# Installing missing --relative-to option on Mac:
# On Mac: REALPATH := /opt/homebrew/opt/coreutils/libexec/gnubin/realpath
#/opt/homebrew/opt/coreutils/libexec/gnubin/realpath: coreutils
#coreutils: homebrew
#	brew install coreutils
#homebrew: /opt/homebrew/bin/brew
#/opt/homebrew/bin/brew:
#	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
#	(echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
#	eval "$(/opt/homebrew/bin/brew shellenv)"
ifeq ($(shell which realpath),/usr/bin/realpath)
  # Use a git-project common worktree
  _{_}_HERE_DIR := $(shell realpath --relative-to=$(_{_}_HOME_DIR) $(_{_}_DIR) )
else
  # Use a local worktree
  _{_}_HERE_DIR := $(_{_}_DIR)
endif

_{_}_HERE := $(_{_}_HERE_DIR:%%.=%%)
_{_}_OLD_WORKTREE := $(_{_}_HOME)$(__{_}_BUILD)$(_{_}_BASELINE)/$(_{_}_NAME)/
_{_}_OLD := $(_{_}_OLD_WORKTREE)$(_{_}_HERE)

# Create status lines
ifeq ($(NORMAL),)
  NORMAL := `tput sgr0`
  RED := `tput setaf 1`
  GREEN := `tput setaf 2`
  YELLOW := `tput setaf 3`
  BLUE := `tput setaf 4`
  REVERSED := `tput rev`
endif
_{_}_BRANCH_STATUS := $(if $(_{_}_ADD),$(RED)$(_{_}_ADD)$(NORMAL))
_{_}_BRANCH_STATUS += $(if $(_{_}_MODIFIED),$(BLUE)$(_{_}_MODIFIED)$(NORMAL))
_{_}_BRANCH_STATUS += $(if $(_{_}_REMOVE),$(REVERSED)$(_{_}_REMOVE)$(NORMAL))
_{_}_COMMIT_INFO := $(shell git log -1 --oneline $(_{_}_DIR))
_{_}_BRANCH_STATUS += $(_{_}_COMMIT_INFO)
ifeq ($(filter v%%,$(_{_}_BASELINE)),)
  _{_}_BASELINE_INFO := $(shell git show --oneline -s $(_{_}_BASELINE))
else
  _{_}_BASELINE_INFO := $(strip $(shell git tag --list $(_{_}_BASELINE) -n1))
endif
_{_}_CHANGES := $(_{_}_BASELINE_INFO) --> $(_{_}_BRANCH_STATUS)
_{_}_CHANGES_AUDIT := $(_{_}_BASELINE_INFO) -->
_{_}_CHANGES_AUDIT += $(_{_}_ADD)
_{_}_CHANGES_AUDIT += $(_{_}_MODIFIED)
_{_}_CHANGES_AUDIT += $(_{_}_COMMIT_INFO)

# List all installation and test targets
_{_}_SRCS := $(_{_}_S)
_{_}_CXX := $(_{_}_C)
_{_}_CXX += $(_{_}_CPP)
_{_}_SRCS += $(_{_}_CXX)
_{_}_CODE := $(_{_}_SRCS)
_{_}_CODE += $(_{_}_PY)
ifneq ($(strip $(_{_}_SRCS)),)
  _{_}_EXE := $(_{_}){_}
  _{_}_EXE_TESTED := $(_{_}_BUILD){_}.tested
endif
_{_}_BRINGUP := $(_{_}_PY:$(_{_})%%=$(_{_}_BUILD)%%.bringup)
_{_}_TESTED := $(_{_}_EXE_TESTED)
_{_}_TESTED += $(_{_}_PY:$(_{_})%%=$(_{_}_BUILD)%%.tested)
_{_}_PRETESTED := $(_{_}_TESTED)
_{_}_TESTED += $(_{_}_MD:$(_{_})%%=$(_{_}_BUILD)%%.sh-test.tested)

# Prepare for compilation
_{_}_INC_DIRS := $(_{_}_DIR)
_{_}_LDFLAGS := $(LDFLAGS)
ifneq ($(strip $(_{_}_S)),)
  _{_}_LDFLAGS += -nostartfiles -no-pie
endif
_{_}_CXXFLAGS := $(_{_}_LDFLAGS)
_{_}_CXXFLAGS += -S $(addprefix -I,$(_{_}_INC_DIRS)) -MMD -MP -Wall
_{_}_CFLAGS := $(_{_}_CXXFLAGS)
_{_}_CXXFLAGS += $(CXXFLAGS)
_{_}_CFLAGS += $(CFLAGS)
_{_}_COBJS := $(_{_}_CXX:$(_{_})%%=$(_{_}_BUILD)%%.s)
_{_}_DEPS := $(_{_}_COBJS:.s=.d)
_{_}_OBJS := $(_{_}_S)
_{_}_OBJS += $(_{_}_COBJS)
_{_}_EXES := $(_{_}_EXE)
_{_}_EXES += $(_{_}_PY)

# Prepare for bringup
_{_}_PYTHON := $(_{_}_DIR)venv/bin/python
_{_}_PY_MK := $(_{_}_PY:$(_{_})%%=$(_{_}_BUILD)%%.mk)
_{_}_DEPS += $(_{_}_PY_MK)

# Prepare for reporting
_{_}_LOGIC := $(_{_}_MAKEFILE)
_{_}_LOGIC += $(_{_}_CODE)
_{_}_RESULT := $(_{_}_PY_MK)
_{_}_RESULT += $(_{_}_BRINGUP)
_{_}_RESULT += $(_{_}_TESTED)
_{_}_REPORT := $(_{_}_BUILD)report-details.md
_{_}_REPORT += $(_{_}_LOGIC:$(_{_})%%=$(_{_}_BUILD)%%.md)
_{_}_REPORT += $(_{_}_RESULT:%%=%%.md)

# Default rule
.DELETE_ON_ERROR:
$(_{_})all: $(_{_})bringup

$(_{_})bringup: $(_{_}_EXE) $(_{_}_BRINGUP)
$(_{_})tested: $(_{_}_TESTED)

# build/*.c.s: Compile C
$(_{_}_BUILD)%%.c.s: $(_{_})%%.c
	$(CXX) $(_{_}_CFLAGS) -c $< -o $@

# build/*.cpp.s: Compile C++
$(_{_}_BUILD)%%.cpp.s: $(_{_})%%.cpp
	$(CXX) $(_{_}_CXXFLAGS) -c $< -o $@

# Link executable
$(_{_}){_}: $(_{_}_OBJS)
	$(CC) $(_{_}_LDFLAGS) $^ -o $@

# Test executable:
$(_{_}_BUILD){_}.tested: $(_{_}){_}
	true | ./$< > $@ || (cat $@ && false)

# Check Python 3.9 syntax
$(_{_})syntax: $(_{_}_BUILD)syntax
$(_{_}_BUILD)syntax: $(_{_}_PY) | $(_{_})venv/bin/ruff
	$(_{_}_PYTHON) -m ruff \\
	    --select=E9,F63,F7,F82 \\
	    --target-version=py39 $(_{_}_DIR) > $@ || (cat $@ && false)
$(_{_})venv/bin/ruff: | $(_{_}_PYTHON)
	$(_{_}_PYTHON) -m pip install ruff
$(_{_})venv $(_{_}_PYTHON):
	( cd $(_{_}_DIR) && python3 -m venv venv )
	$(_{_}_PYTHON) -m pip install --upgrade pip
	$(_{_}_PYTHON) -m pip install requests  # Needed by -m makemake --prompt

# Check Python 3.9 style
$(_{_})style: $(_{_}_BUILD)style
$(_{_}_BUILD)style: $(_{_}_BUILD)syntax
	$(_{_}_PYTHON) -m ruff --fix --target-version=py39 $(_{_}_DIR) > $@ \\
	|| (cat $@ && false)

# Build a recipy for $(_{_}_BUILD)%%.py.bringup
$(_{_}_BUILD)%%.py.mk: $(_{_})%%.py
	( cd $(_{_}_DIR) && PYTHONPATH=$(_{_}_DIR) python3 $*.py --generic --dep $(__{_}_BUILD)$*.py.mk ) ; \\
	if [ ! -f $@ ]; then echo "\\$$(_{_}_BUILD)$*.py.bringup:; touch \\$$@" >$@; fi

# Check Python and command line usage examples in .py files
$(_{_}_BUILD)%%.py.tested: $(_{_})%%.py $(_{_}_BUILD)%%.py.mk \\
  $(_{_}_BUILD)style $(_{_}_BUILD)%%.py.bringup $(_{_}_EXE_TESTED)
	$(_{_}_PYTHON) $< --test > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$(_{_}_BUILD)%%.sh-test.tested: $(_{_}_BUILD)%%.sh-test $(_{_}_PRETESTED) | \\
  $(_{_})makemake.py
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $(_{_}_DIR) && python3 -m makemake --timeout 60 --sh-test \
	    $(__{_}_BUILD)$*.sh-test ) > $$tmp && mv $$tmp $@
# ToDo: depend on pandoc and jq
# On Mac: 
#jq: /opt/homebrew/bin/jq
#/opt/homebrew/bin/jq: homebrew; brew install jq
# On Ubuntu: 
#jq: /usr/bin/jq
#/usr/bin/jq: ; sudo apt install -y jq
$(_{_}_BUILD)%%.md.sh-test: $(_{_})%%.md | #/usr/bin/pandoc /usr/bin/jq
	pandoc -i $< -t json --preserve-tabs | \
	jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | \
select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && \\
	truncate -s -1 $@

# Document all source codes:
$(_{_})s: $(_{_}_SOURCE)
	@$(foreach s,$^,echo "___ $(s): ____" && cat $(s) ; )

# Document all assembly codes linked into $(_{_}){_}.
$(_{_})a: $(_{_}_OBJS)
	@$(foreach a,$^,echo "___ $(a): ____" && cat $(a) ; )

# Document all dependencies.
$(_{_})d: $(_{_}_DEPS)
	@$(foreach d,$^,echo "___ $(d): ____" && cat $(d) ; )

# Document all bringups.
$(_{_})b: $(_{_}_BRINGUP)
	@$(foreach b,$^,echo "___ $(b) ____" && cat $(b) ; )

# Document all test results.
$(_{_})report: $(_{_}_BUILD)report.txt
	@cat $<
$(_{_}_BUILD)report.txt: $(_{_}_TESTED)
	( $(foreach t,$^,echo "___ $(t): ____" && cat $(t) ; ) ) > $@

# Make a standalone html, pdf, gfm or dzslides document.
# ToDo: install xelatex
# On Mac:
# /Library/TeX/texbin/tex: homebrew
#	brew install --cask basictex
#	eval "$(/usr/libexec/path_helper)"
$(_{_})%%.gfm: $(_{_}_BUILD)%%.md
	pandoc --standalone -t $(patsubst .%%,%%,$(suffix $@)) -o $@ $^ \\
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%%an'`"
# WIP add missing dependencies
# for Mac: | \\
#  ~/Library/Fonts/Carlito-Regular.ttf \\
#  ~/Library/Fonts/Cousine-Regular.ttf \\
#  /opt/homebrew/bin/pandoc /Library/TeX/texbin/xelatex
# for Linux: | \\
#  /usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf \\
#  /usr/share/fonts/truetype/cousine/Cousine-Regular.ttf \\
#  /usr/bin/pandoc /usr/bin/xelatex
$(_{_})%%.html $(_{_})%%.pdf $(_{_})%%.dzslides: $(_{_}_BUILD)%%.md
	pandoc --standalone -t $(patsubst .%%,%%,$(suffix $@)) -o $@ $^ \\
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%%an'`" \\
	       -V min-width=80%%\!important -V geometry:margin=1in \\
	       --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"
ifndef pandoc
pandoc:=/usr/bin/pandoc
# Make doesn't detect /usr/bin/pandoc: A phony target that may actually exist.
# ToDo on Mac: /opt/homebrew/bin/pandoc: homebrew; brew install pandoc
# ToDo on Ubuntu: 
#	sudo apt update && sudo apt upgrade && sudo apt install -y git make python3 python3.10-venv build-essential pandoc libc-bin texlive-xetex fonts-crosextra-carlito
#	make /usr/share/fonts/truetype/cousine/Cousine-Regular.ttf
# ToDo on Windows: install pandoc
#/usr/bin/pandoc: pandoc-3.1.6.1-1-amd64.deb
#	@if [ ! -e /usr/bin/pandoc ] ; then (sudo dpkg -i $< ) ; fi
#pandoc-%%-1-amd64.deb:
#	@if [ ! -e /usr/bin/pandoc ] ; then ( \\
#	  echo "Need a small general text processing framework: pandoc" && \\
#	  curl https://github.com/jgm/pandoc/releases/download/$*/pandoc-$*-1-amd64.deb -o $@\\
#	) ; fi
/usr/bin/xelatex:
	# Need a modern pdf generation framework: xelatex
	sudo apt-get update && sudo apt install -y texlive-xetex
/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf:
	# Need a more screen-readable normal font: carlito
	sudo apt-get install fonts-crosextra-carlito
~/Library/Fonts/%%-Regular.ttf: # Mac user font
	# Installing $< font family $* into $(dir $@)
	( cd $(dir $@) && \\
	  family=`echo $* | tr A-Z a-z` && \\
	  fonts=https://raw.githubusercontent.com/google/fonts/main/$</$$family && \\
	  curl $$fonts/$*-Bold.ttf -o $*-Bold.ttf && \\
	  curl $$fonts/$*-BoldItalic.ttf -o $*-BoldItalic.ttf && \\
	  curl $$fonts/$*-Italic.ttf -o $*-Italic.ttf && \\
	  curl $$fonts/$*-Regular.ttf -o $*-Regular.ttf )
~/Library/Fonts/Carlito-Regular.ttf: ofl
~/Library/Fonts/Cousine-Regular.ttf: apache
ofl apache:
	touch $@
/usr/share/fonts/truetype/%%-Regular.ttf: # Ubuntu shared font
	# Installing font family $(notdir $*) into $(dir $@)
	( sudo mkdir -p $(dir $@) && cd $(dir $@) && \\
	  fonts=https://raw.githubusercontent.com/google/fonts/main/apache && \\
	  sudo curl $$fonts/$*/DESCRIPTION.en_us.html -o DESCRIPTION.en_us.html && \\
	  sudo curl $$fonts/$*-Bold.ttf -o $(notdir $*)-Bold.ttf && \\
	  sudo curl $$fonts/$*-BoldItalic.ttf -o $(notdir $*)-BoldItalic.ttf && \\
	  sudo curl $$fonts/$*-Italic.ttf -o $(notdir $*)-Italic.ttf && \\
	  sudo curl $$fonts/$*-Regular.ttf -o $(notdir $*)-Regular.ttf )
/usr/bin/jq:
	# Need a tool to filter json: jq
	sudo apt install -y jq
endif

# Make a markdown document.
_{_}link< = [$(<:$(_{dir})%%=%%)]($(<:$(_{dir})%%=%%))
_{_}_h :=\\n---\\n\\n\#
_{_}~~~. =\\\\\\footnotesize\\n~~~ {{$1}}
_{_}~~~sh :=$(call _{_}~~~.,.sh)
_{_}~~~ :=~~~\\n\\\\\\normalsize\\n
$(_{_}_BUILD)Makefile.md: $(_{_})Makefile
	( echo "$(_{_}_h)## [$(_{_}link<)" && \\
	  echo "$(call _{_}~~~.,.mk)" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.md: $(_{_})%%
	( echo "$(_{_}_h)## [$(_{_}link<)" && \\
	  echo "$(call _{_}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.md: $(_{_}_BUILD)%%
	( echo "$(_{_}_h)## [$(_{_}link<)" && \\
	  echo "$(call _{_}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.bringup.md: $(_{_}_BUILD)%%.bringup
	( echo "$(_{_}_h)## [$(_{_}link<)" && \\
	  echo "$(_{_}~~~sh)" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.tested.md: $(_{_}_BUILD)%%.tested
	( echo "$(_{_}_h)## [$(_{_}link<)" && \\
	  echo "$(_{_}~~~sh)" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@

# Report the project.
$(_{_})%%: $(_{_})report.%%
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BRANCH_STATUS)"
$(_{_})slides: $(_{_})slides.html
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BRANCH_STATUS)"
$(_{_})slides.html: $(_{_})report.dzslides
	mv $< $@
$(_{_})report.html $(_{_})report.pdf $(_{_})report.gfm \\
  $(_{_})report.dzslides: $(_{_}_MD) $(_{_}_REPORT)
_{_}_file = $(foreach _,$(_{_}_$1),[\\`$_\\`]($_))
_{_}_exe = $(foreach _,$(_{_}_$1),[\\`./$_\\`]($_))
_{_}_h_fixup :=sed -E '/^$$|[.]{{3}}/d'
$(_{_}_BUILD)report.md: $(_{_}_BUILD)report.txt
	echo "A build-here include-from-anywhere project \
based on [makemake](https://github.com/joakimbits/normalize)." > $@
	echo "\\n- \\`make report pdf html slides review audit\\`" >> $@
ifneq ($(strip $(_{_}_EXE)),)
	echo "- \\`./{_}\\`: $(subst $(_{_}),,$(call _{_}_file,SRCS))" >> $@
endif
ifneq ($(strip $(_{_}_PY)),)
	echo "- $(subst $(_{_}),,$(call _{_}_exe,PY))" >> $@
endif
	echo "$(_{_}_h)## Installation" >> $@
	echo "$(_{_}~~~sh)" >> $@
	echo "\\$$ make" >> $@
	echo "$(_{_}~~~)" >> $@
ifneq ($(strip $(_{_}_EXE)),)
	echo "- Installs \\`./{_}\\`." >> $@
endif
ifneq ($(strip $(_{_}_PY)),)
	echo "- Installs \\`./venv\\`." >> $@
	echo "- Installs $(subst $(_{_}),,$(call _{_}_exe,PY))." >> $@
endif
ifneq ($(_{_}_EXES),)
	echo "$(_{_}_h)## Usage" >> $@
	echo "$(_{_}~~~sh)" >> $@
	for x in $(subst $(_{_}_DIR),,$(_{_}_EXES)) ; do \\
	  echo "\\$$ true | ./$$x -h | $(_{_}_h_fixup)" >> $@ && \\
	  ( cd $(_{_}_DIR) && true | ./$$x -h ) > $@.tmp && \\
	  $(_{_}_h_fixup) $@.tmp >> $@ && rm $@.tmp ; \\
	done
	echo >> $@
	echo "$(_{_}~~~)" >> $@
	echo "$(_{_}_h)## Test" >> $@
	echo "$(_{_}~~~sh)" >> $@
	echo "\\$$ make tested" >> $@
	echo "$(_{_}~~~)" >> $@
endif
ifneq ($(strip $(_{_}_EXE)),)
	echo "- Tests \\`./{_}\\`." >> $@
endif
ifneq ($(strip $(_{_}_PY)),)
	echo "- Verifies style and doctests in\
 $(subst $(_{_}_DIR),,$(call _{_}_file,PY))." >> $@
endif
ifneq ($(strip $(_{_}_MD)),)
	echo "- Verifies doctests in $(subst $(_{_}_DIR),,$(call _{_}_file,MD))." >> $@
endif
ifneq ($(strip $(_{_}_CODE)),)
	echo "$(_{_}_h)## Result" >> $@
	echo "$(_{_}~~~sh)" >> $@
	echo "\\$$ make report" >> $@
	( cd $(_{_}_DIR) && $(MAKE) report --no-print-directory ) >> $@
	echo "$(_{_}~~~)" >> $@
	echo "\\n---\\n" >> $@
$(_{_}_BUILD)report-details.md:
	echo "$(_{_}_h)# Source code, installation and test result" >> $@
endif

# Build an old worktree that is shared by all projects in this git
ifndef _OLD_WORKTREE
_OLD_WORKTREE := $(_{_}_OLD_WORKTREE)
$(_OLD_WORKTREE):
	git worktree add -d $(_OLD_WORKTREE) $(_{dir}_BASELINE)
endif

# Document last release.
$(_{_})old: $(_{_}_OLD)report.gfm
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BASELINE_INFO)"
$(_{_}_OLD)report.gfm: $(_OLD_WORKTREE)
	mkdir -p $(dir $@) && ( cd $(dir $@) && $(MAKE) report.gfm --no-print-directory ) || touch $@

# Use GPT for a release review.
$(_{_})%%: $(_{_}_BUILD)%%.diff
	cat $<
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_CHANGES)"
$(_{_}_BUILD)audit.diff: $(_{_}_BUILD)prompt.diff | $(_{_}_PYTHON)
	cat $< > $@
	$(_{_}_PYTHON) -m makemake --prompt $< $(_{_}_MODEL) $(_{_}_TEMPERATURE)\
 $(_{_}_BEARER_rot13) >> $@
$(_{_}_BUILD)prompt.diff: $(_{_}_BUILD)review.diff
	python3 -m makemake -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $(_{_})review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$(_{_}_BUILD)review.diff: $(_{_}_BUILD)files.diff $(_{_}_BUILD)comments.diff\
  $(_{_}_BUILD)report.diff
	cat $^ > $@
$(_{_}_BUILD)files.diff:
	echo "# List of git comments since $(_{_}_CHANGES_AUDIT)" > $@
$(_{_}_BUILD)comments.diff:
	echo "git --no-pager log --no-merges $(_{_}_BASELINE)..HEAD $(_{_}_DIR)" > $@
	git --no-pager log --no-merges $(_{_}_BASELINE)..HEAD $(_{_}_DIR) >> $@
$(_{_}_BUILD)report.diff: $(_{_}_OLD)report.gfm $(_{_})report.gfm
	echo "diff -u -U 100000 $< $(word 2,$^) | fold-unchanged" > $@
	( diff -u -U 100000 $< $(word 2,$^) | csplit -s - /----/ '{{*}}' && \\
	  parts=`ls xx**` && \\
	  changed_parts=`grep -l -e '^-' -e '^+' xx**` && \\
	  for part in $$parts ; do \\
	    if `echo "$$changed_parts" | fgrep -wq "$$part" \\
	    || test "$$(wc $$part)" = "1"` ; then \\
	      python3 -m makemake --split $$part '\\n \\n \\n' 's%%02d' && \\
	      sections=`ls s**` && \\
	      changed_sections=`grep -l -e '^-' -e '^+' s**` && \\
	      for section in $$sections ; do \\
	        if `echo "$$changed_sections" | fgrep -wq "$$section" \\
	        || test "$$(wc $$section)" = "1"` ; then \\
	          python3 -m makemake --split $$section '\\n \\n' 'p%%02d' && \\
	          paragraphs=`ls p**` && \\
	          changed_paragraphs=`grep -l -e '^-' -e '^+' p**` && \\
	          for paragraph in $$paragraphs ; do \\
	            if `echo "$$changed_paragraphs" | fgrep -wq "$$paragraph"` ; then \\
	              cat $$paragraph ; echo ; echo ; \\
	            else \\
	              echo "$$(head -1 $$paragraph) ..." ; fi ; \\
	            done ; \\
	          rm p** ; \\
	        else \\
	          echo "$$(head -1 $$section) ..." ; fi ; \\
	        done ; \\
	      rm s** ; \\
	    else \\
	      echo "$$(sed -n '3p' $$part) ..." ; fi ; \\
	    done ; \\
	  rm xx**; ) >> $@

# Include the autogenerated dependencies
-include $(_{_}_DEPS)
endif  # _{_}_DIR
"""  # noqa: E101

COMMENT_GROUP_PATTERN = re.compile("(\s*#.*)?$")


def make_rule(rule, commands, file=sys.stdout):
    """Make a Makefile build recipy"""
    print(rule, file=file)
    print('\t' + " \\\n\t".join(commands), file=file)


def build_commands(doc, heading=None, embed="%s", end="", pip=""):
    """Extract shell commands and pip requirements"""
    if not doc:
        return []

    if heading:
        before_after = doc.split(f"{heading}\n", maxsplit=1)
        doc = before_after[1] if len(before_after) >= 2 else ""

    commands = []
    if doc:
        for line in doc.split('\n'):
            command_lines, comment_lines, output_lines = (
                commands[-1] if commands else ([], [], []))
            command, comment, _ = re.split(COMMENT_GROUP_PATTERN, line, maxsplit=1)
            if comment is None:
                comment = ""

            if command in ('$', '>') and (not comment or comment.startswith(' ')):
                command += ' '
                comment = comment[1:]

            if command[:2] == '$ ':
                if command[2:]:
                    commands.append(([embed % command[2:] + end], [comment], []))
            elif command[:2] == '> ':
                if end:
                    command_lines[-1] = command_lines[-1][:-len(end)]
                command_lines.append(command[2:] + end)
                comment_lines.append(comment)
            elif (command_lines and not output_lines and
                  command_lines[-1] and command_lines[-1][-1] == '\\'):
                command_lines[-1] = command_lines[-1][:-len(end)]
                command_lines.append(embed % command + end)
                comment_lines.append(comment)
            elif command_lines and not pip:
                output_lines.append(command)
            elif command and pip:
                commands.append(([f"{pip} install " + command], [comment], []))

    return commands


def run_command_examples(commands, timeout=3):
    """Run extracted shell commands and verify output"""
    if not commands:
        return

    import subprocess

    for i, (command_lines, comment_lines, output_lines) in enumerate(commands):
        command = "\n".join(map("".join, zip(command_lines, comment_lines)))
        if module_dir:
            command = f"( cd {module_dir} && {command} )"
        output = "\n".join(output_lines)
        result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                timeout=timeout)
        assert not result.returncode, (
            f"Example {i + 1} failed: $ {command}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}")
        received = result.stdout or ""
        assert received == output, (
            f"Example {i + 1}: $ {command}\n"
            f"Expected: {repr(output)}\n"
            f"Received: {repr(received)}")


if parent_module.__name__ == '__main__':
    dependencies = '--makemake' in sys.argv[1:]
    generic_dependencies = '--generic' in sys.argv[1:]
    dep_path = '--dep' in sys.argv[1:]
    if dependencies or generic_dependencies or dep_path:
        assert len(sys.argv) == sum([1, dependencies, generic_dependencies,
                                     dep_path * 2]), (
            sys.argv, [1, dependencies, generic_dependencies,
                       dep_path * 2])

        if dep_path:
            dep_file = sys.argv[sys.argv.index('--dep', 1) + 1]
            assert dep_file[:2] != "__", sys.argv
            dep_dir, dep_filename = os.path.split(dep_file)
            dep_dir_now = dep_dir
            if dep_dir:
                prefix = _ + "/"
                dep_dir = dep_dir + "/"
                if dep_dir.startswith(prefix):
                    dep_dir = dep_dir[len(prefix):]
        else:
            dep_dir_now = dep_dir = 'build/'
            dep_filename = f'{module_py}.mk'
            dep_file = f'build/{module_py}.mk'

        if generic_dependencies:
            if dependencies:
                print(MAKEFILE_FROM_BUILD_DIR % dep_dir)
            pattern = '%'
            source = '$<'
            stem = '$*'
            python = f'$(_{_}_PYTHON)'
            src_dir = f'$(_{_})'
            build_dir = f'$(_{_}_BUILD)'
            build_dir_var_value = f"{src_dir}{dep_dir}"
            generic = " --generic"
        else:
            pattern = module
            source = module_path
            stem = module
            python = 'python3'
            src_dir = ""
            build_dir = dep_dir
            generic = ""

        if generic_dependencies:
            embed = f"( cd $(_{_}_DIR) && %s"
            end = " )"
            rules = []  # The generic rules are already printed
        else:
            embed = "%s"
            end = ""
            rules = [
                (f"all: {build_dir}{pattern}.py.tested",
                 [])]
            if dep_path:
                rules += [
                    ((f"{build_dir}{pattern}.py.tested: {src_dir}{pattern}.py"
                      f" {dep_file} {build_dir}{pattern}.py.bringup"),
                     [f"{python} {source} --test > $@"]),
                    (f"{dep_file}: {src_dir}{pattern}.py",
                     [f"{python} {source} --dep $@{generic}"])]
            else:
                rules.append(
                    ((f"{build_dir}{pattern}.py.tested: {src_dir}{pattern}.py"
                      f" {build_dir}{pattern}.py.bringup"),
                     [f"{python} {source} --test > $@"]))

        commands = []
        bringups = build_commands(parent_module.__doc__, '\nDependencies:', embed, end,
                                  pip=f"{python} -m pip")
        bringups.append((['chmod +x $<'], [''], []))
        op = ">"
        remaining = len(bringups)
        for command_lines, comment_lines, output_lines in bringups:
            remaining -= 1
            glue = " &&" if remaining else ""
            commands += command_lines[:-1]
            commands.append(f'{command_lines[-1]} {op} $@{glue}')
            op = '>>'

        bringup_rule = f"{build_dir}{module}.py.bringup: {src_dir}{module}.py"
        if generic_dependencies or dep_path:
            bringup_rule += f" {build_dir}{dep_filename}"
            if generic_dependencies:
                bringup_rule += f" $(_{_}_PYTHON)"
        else:
            commands = [f"mkdir {build_dir}" + (" &&" if commands else "")] + commands

        rules.append(
            (bringup_rule,
             commands))

        if not commands:
            commands += ["touch $@"]

        for rule, commands in rules:
            if rule == bringup_rule and (dep_path or generic_dependencies):
                if not generic_dependencies:
                    print(f"include {build_dir}{dep_filename}")

                if dep_dir and not os.path.exists(dep_dir_now):
                    os.makedirs(dep_dir_now)

                if dep_path:
                    with open(dep_file, 'w+') as dep:
                        make_rule(rule, commands, file=dep)
            elif dependencies:
                make_rule(rule, commands)

        exit(0)


class Test(Action):
    """Verify usage examples and exit"""

    def __call__(self, parser, args, values, option_string=None):
        import doctest

        try:
            result = doctest.testmod(
                parent_module,
                optionflags=(doctest.ELLIPSIS |
                             doctest.NORMALIZE_WHITESPACE |
                             doctest.FAIL_FAST |
                             doctest.IGNORE_EXCEPTION_DETAIL))
            assert result.failed == 0, result
            print(f"All {result.attempted} python usage examples PASS", )
            examples = build_commands(parser.epilog, "Examples:")
            run_command_examples(examples, args.timeout)
            print(f"All {len(examples)} command usage examples PASS")
        except AssertionError as err:
            print(err, file=sys.stderr)
            exit(1)

        exit(0)


class ShTest(Action):
    """Test command usage examples in a file, and exit"""
    err = False

    def __call__(self, parser, args, values, option_string=None):
        file, = values
        examples = build_commands(open(file).read())
        lock = file + '.lock'
        try:
            os.mkdir(lock)
            run_command_examples(examples, args.timeout)
        except FileExistsError:
            print("Recursive usage of", lock, file=sys.stderr)
        except AssertionError as err:
            print(err, file=sys.stderr)
            self.err = err

        try:
            os.rmdir(lock)
        except FileNotFoundError:
            pass

        if self.err:
            exit(1)

        print(f"All {len(examples)} command usage examples PASS")
        exit(0)


class Command(Action):
    """Execute a program string and exit"""

    def __call__(self, parser, args, values, option_string=None):
        program, = values
        exec(program, parent_module.__dict__, locals())
        exit(0)


class Split(Action):
    """Split FILE by SEPARATOR into files with PATTERN %% 0, 1 ..., and exit"""

    def __call__(self, parser, args, values, option_string=None):
        file, escaped_separator, pattern = values
        separator = bytes(escaped_separator, "utf-8").decode("unicode_escape")
        for i, s in enumerate(open(file).read().split(separator)):
            open(pattern % i, 'w').write(s)


class Prompt(Action):
    """Print an openai continuation from a promt file, model, temperature and bearer
    rot13 key, and exit"""

    def __call__(self, parser, args, values, option_string=None):
        import requests
        import json
        import codecs

        file, model, temperature, key = values
        prompt = open(file).read()
        key = codecs.decode(key, 'rot13')
        data = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": prompt}],
            "temperature": float(temperature)
        }
        data = json.dumps(data).encode('UTF-8')
        headers = {
            'Content-Type': 'application/json',
            'Accept-Charset': 'UTF-8',
            'Authorization': f"Bearer {key}"
        }
        url = 'https://api.openai.com/v1/chat/completions'
        r = requests.post(url, data=data, headers=headers)
        status = r.status_code, r.reason, r.text
        assert status[:2] == (200, 'OK'), status
        c = json.loads(r.content)
        u = c['usage']
        print(c['model'], c['object'], c['id'],
              f"prompted {u['prompt_tokens']} -> completed {u['completion_tokens']}:")
        print(c['choices'][0]['message']['content'])
        exit(0)

def brief(*callables):
    """Return a summary of all callables"""
    usage = (parent_module.__doc__ or '').split('\nDependencies:\n')[0]
    if not callables:
        callables = [parent_module]

    for fun in callables:
        description = (
            pydoc.describe(fun).replace('\n\n', '\n') +
            f": {pydoc.splitdoc(fun.__doc__ or '')[0]}"
        ) if fun != parent_module else ""
        for attr in dir(fun):
            if attr[0] == '_':
                continue

            val = getattr(fun, attr)
            if callable(val):
                description += '\n\t'
                description += pydoc.describe(val).replace('\n\n', '\n')
                description += f": {pydoc.splitdoc(val.__doc__ or '')[0]}"

        usage += f"\n{description}"

    return usage


def add_arguments(argparser):
    argparser.add_argument('--makemake', action='store_true', help=(
        f"Print Makefile for {module_path}, and exit"))
    argparser.add_argument('--generic', action='store_true', help=(
        f"Print generic Makefile for {module_path}, and exit"))
    argparser.add_argument('--dep', action='store', help=(
        f"Build a {module}.dep target, print its Makefile include statement, and exit"))
    argparser.add_argument('-c', nargs=1, action=Command, help=Command.__doc__)
    argparser.add_argument('--timeout', type=int, default=3, help=(
        "Test timeout in seconds (3)"))
    argparser.add_argument('--test', nargs=0, action=Test, help=Test.__doc__)
    argparser.add_argument('--sh-test', nargs=1, action=ShTest, help=ShTest.__doc__)
    argparser.add_argument('--split', nargs=3, action=Split, help=Split.__doc__)
    argparser.add_argument('--prompt', nargs=4, action=Prompt, help=Prompt.__doc__)


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=brief(),
        epilog="""Examples:
$ python3 makemake.py --dep makemake.dep
include makemake.dep

$ cat makemake.dep
makemake.py.bringup: makemake.py makemake.dep
	python3 -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version' > $@"""
               """ && \\
	python3 -m pip install requests >> $@ && \\
	chmod +x $< >> $@

$ python3 makemake.py --dep makemake.dep --makemake
all: makemake.py.tested
	
makemake.py.tested: makemake.py makemake.dep makemake.py.bringup
	python3 makemake.py --test > $@
makemake.dep: makemake.py
	python3 makemake.py --dep $@
include makemake.dep

$ python3 -m makemake -c "print(module_py)"
makemake.py
""")
    add_arguments(argparser)
    args = argparser.parse_args()
