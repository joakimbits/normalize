#!venv/python.exe
"""Print a Makefile for handling a python module and exit

Adds the following command line options to the main module:

--makemake: Print a Makefile for bringup and test of the parent module.
--generic: Generalize it to make everything that is makeable within the parent module directory, and from anywhere.
--dep <file>: Create a separate Makefile for bringup of the parent module, and set the build directory to its parent
  directory.

Makes it easy to add the following command line options to the parent module:

--timeout: Time in seconds before giving up on a command-line test.
--sh-test <file>: Test command line usage examples in a file and exit.
--test: Verify python and command line usage examples in the module and exit.
-c <string>: Execute a program string in the module and exit.
--prompt <file> <openai model> <T> <rot13-encoded key>: Print a GPT continuation of the file and exit.


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
    tooled.txt: tools/tool.py tools/build/tool.py.bringup  # (1, 4)
        $(_tools_PYTHON) $< > $@  # (5)
    tools/Makefile:
        $(PYTHON) tools/tool.py --makemake --generic >$@  # (2)
    -include tools/Makefile  # (0, 3)

$ make tooled.txt

How it works:
    1. Make softly fails -include tools/Makefile, builds it, restarts, and now includes it.
    2. Make wants tooled.txt, needs tools/build/tool.py.bringup that needs $(_tools_PYTHON).
    3. Make builds $(_tools_PYTHON), tools/build/tool.py.bringup and finally tooled.txt.
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
$ $(PYTHON) -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version'
requests  # Needed for the --prompt option
"""

import platform
import sys
import os
import re
from argparse import Action
import pydoc

parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
cwd = os.getcwd()
_ = os.path.split(cwd)[1]
module_path = os.path.relpath(os.path.abspath(sys.argv[0]))
module_dir, module_py = os.path.split(module_path)
makemake_py = os.path.relpath(os.path.abspath(__file__), os.path.abspath(module_dir))
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

Here is the command you should use for releasing the software:

    $ tag=<new version> git tag -a $$tag -m "$$tag\\n\\n<release summary>")

Chose a new semantic version number that is larger than the previously released version
for the <new version>. Summarize the commit comments and project changes I printed
below in a more user-friendly style for the <release summary>.

If you can do this well I will consider automating releases with your help. Otherwise
I will need to wait for gpt-4. Thank you for your service.
---
"""

MAKEFILE_FROM_BUILD_DIR = f"""# {_}$ {" ".join(sys.argv)}
ifeq ($(_{_}_DIR),)

# Configure a GPT _{_}_MODEL to use for `audit`
#  - A large-context openai model suitable for code review
#  - A rot13 encoded openai Bearer key for its GPT session.
#  - A temperature for its openai continuation.
_{_}_MODEL ?= gpt-3.5-turbo-16k
_{_}_BEARER_rot13 ?= fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj
_{_}_TEMPERATURE ?= 0.7

# The builder's home directory and name
H := $(shell echo ~)
I := $(shell whoami)

# Workaround Windows feature: Windows domain in whoami
I := $(subst \\, ,$I)
ifneq ($(words $I),1)
    DOMAIN := $(firstword $(WHOAMI))
    I := $(lastword $I)
endif

# Workaround Windows WSL1 bug: Recursive make shell believes it is git bash on Windows
ifeq ($H,/Users/$I)
    H := /home/$I
endif

# Configure a base PYTHON to use. It can be one of:
#  - `python3` on Ubuntu or Mac,
#  - `python.exe` in Windows from WSL Ubuntu, or
#  - `python` on Windows.
#  - or any given PYTHON.
ifeq ($H,/home/$I)
    PYTHON ?= python3
    VENV_PYTHON ?= bin/python3
    
    # Workaround Windows WSL bridge bug: Timeout on ipv6 internet routes - slows down pip.
    ifneq ($(shell echo $$WSL_DISTRO_NAME),)
        SPEEDUP_WSL_DNS ?= $H/use_windows_dns.sh $?/pip
        SPEEDUP_WSL_PIP ?= DISPLAY= #
        SPEEDUP_WSL_VENV ?= DISPLAY= $(_{_}_PYTHON) -m pip install --upgrade keyring && #
    endif
else
    PYTHON ?= python
    VENV_PYTHON ?= python.exe
endif
PYTHON := $(shell which $(PYTHON))


### 
# Generic recipies for bringup, testing, reporting and auditing a project
# on any OS and CPU with PYTHON >= Python 3.7.
# Tested on WSL1 and bare Windows x86 and MacOSX Arm64.

# The local python we bringup
__{_}_PYTHON := venv/$(VENV_PYTHON)
_{_}_PYTHON := $(_{_})$(__{_}_PYTHON)

# How to reach here from the current working directory
_{_}_Makefile := $(lastword $(MAKEFILE_LIST))
_{_} := $(patsubst ./,,$(subst \\,/,$(subst C:\\,/c/,$(dir $(_{_}_Makefile)))))
ifeq (,$(_{_}))
    _{_}_DIR := ./
else
    _{_}_DIR := $(_{_})
endif

# Where to build files
__{_}_BUILD := %s
_{_}_BUILD := $(_{_})$(__{_}_BUILD)

# Configure an OS and CPU to build the project for.
ifndef ! 
    OS ?= $(shell $(PYTHON) $(_{_}){makemake_py} -s)
    CPU ?= $(shell $(PYTHON) $(_{_}){makemake_py} -m)
    ifeq ($(OS),MacOSX)
        ! ?= brew install
        ? ?= /opt/homebrew/bin
        FONTS ?= ~/Library/Fonts
        COUSINE := $(FONTS)
        CARLITO := $(FONTS)
    else
        ! ?= sudo apt install -y
        ? ?= /usr/bin
        COUSINE ?= /usr/share/fonts/truetype/cousine
        CARLITO ?= /usr/share/fonts/truetype/crosextra
    endif 
endif

# Notify the user if new rules were built and included, and make therefore restarted
ifeq ($(MAKE_RESTARTS),2)
    ifndef MAKER
        $(info # Hello $I, Welcome to makemake https://github.com/joakimbits/normalize)
    endif
    
    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $(_{_}_BUILD)
    $(info # $(PWD) $(filter-out $(INCLUDING)%%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $(_{_}){makemake_py} $(_{_}_PYTHON) $(_{_}_BUILD))
    INCLUDED := $(MAKEFILE_LIST)
    INCLUDING := $(_{_}_BUILD)

    # Notify the user on abusage of make
    ifneq (0,$(MAKELEVEL))
        $(info # Warning: This is a recursive $(MAKE). Please use global variable names and include instead.)
        $(info # https://aegis.sourceforge.net/auug97.pdf)
        $(info # https://github.com/joakimbits/normalize/blob/main/example/Makefile)
    endif
endif

# Default rule
.DELETE_ON_ERROR:
$(_{_})all: $(_{_})bringup

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
_{_}_PY := $(wildcard $(_{_})*.py)
_{_}_PY := $(subst ./,$(_{_}),$(_{_}_PY))
_{_}_SOURCE += $(_{_}_PY)
_{_}_MD := $(wildcard $(_{_})*.md)
_{_}_SOURCE += $(_{_}_MD)

# Find our git status
_{_}_BRANCH := $(shell git branch --show-current)
_{_}_BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
_{_}_KNOWN := $(addprefix $(_{_}),$(shell cd $(_{_}_DIR) ; git ls-files . ':!:*/*'))
_{_}_ADD := $(filter-out $(_{_}_KNOWN),$(_{_}_SOURCE))
_{_}_MODIFIED := $(shell cd $(_{_}_DIR) && $(PYTHON) {makemake_py} --git-status . M)
_{_}_REMOVE := $(filter-out $(_{_}_SOURCE),$(_{_}_KNOWN))

# Figure out where to checkout an old worktree
_{_}_HOME_DIR := $(dir $(shell git rev-parse --git-common-dir))
_{_}_HOME := $(_{_}_HOME_DIR:./%%=%%)
_{_}_NAME := $(notdir $(abspath $(_{_}_HOME_DIR)))
_{_}_GIT_DIR := $(dir $(shell git rev-parse --git-common-dir))
_{_}_HERE_DIR := $(shell $(PYTHON) $(_{_}){makemake_py} --relpath $(_{_}_GIT_DIR) $(_{_}_DIR))/
_{_}_HERE := $(_{_}_HERE_DIR:%%./=%%)
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
_{_}_CXXFLAGS += -S $(addprefix -I,$(_{_}_INC_DIRS)) -MMD -MP
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

# Convenience targets
.PHONY: $(_{_})bringup $(_{_})tested $(_{_})clean
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
$(_{_}_BUILD)syntax: $(_{_}_PY) | $(_{_})venv/Lib/site-packages/ruff
	$(_{_}_PYTHON) -m ruff \\
	    --select=E9,F63,F7,F82 \\
	    --target-version=py39 $(_{_}_DIR) > $@ || (cat $@ && false)

# Install pip package in the local python:
$(_{_})venv/Lib/site-packages/%%: $(_{_}_PYTHON)
	$(_{_}_PYTHON) -m pip install $*

# Setup a local python:
$(_{_}_PYTHON): $(SPEEDUP_WSL_DNS)
	( cd $(_{_}_DIR) && $(SPEEDUP_WSL_PIP)$(PYTHON) -m venv venv )
	$(SPEEDUP_WSL_VENV)$(SPEEDUP_WSL_PIP)$(_{_}_PYTHON) -m pip install --upgrade pip
	$(SPEEDUP_WSL_PIP)$(_{_}_PYTHON) -m pip install requests  # Needed by -m makemake --prompt

ifndef SPEEDUP_WSL
    SPEEDUP_WSL = 1
    $H/use_windows_dns.sh: ;
	    echo "# Fixing DNS issue in WSL https://gist.github.com/ThePlenkov/6ecf2a43e2b3898e8cd4986d277b5ecf#file-boot-sh" > $@                
	    echo -n "sed -i '/nameserver/d' /etc/resolv.conf && " >> $@
	    echo -n  "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command " >> $@
	    echo -n   "'(Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses | " >> $@
	    echo -n    "ForEach-Object {{ \\"nameserver \\$$_\\" }}' | tr -d '\\\\\\\\r' | " >> $@
	    echo "tee -a /etc/resolv.conf > /dev/null" >> $@
	    sudo sed -i '\|command=$@|d' /etc/wsl.conf
	    echo "command=$@" | sudo tee -a /etc/wsl.conf > /dev/null
	    sudo sh $@
endif

ifndef INSTALL_PIP
    INSTALL_PIP = 1
    $?/pip:
	    $! python3-pip
endif

# Check Python 3.9 style
$(_{_})style: $(_{_}_BUILD)style
$(_{_}_BUILD)style: $(_{_}_BUILD)syntax
	$(_{_}_PYTHON) -m ruff --fix --target-version=py39 $(_{_}_DIR) > $@ ||\
 (cat $@ && false)

# Build a recipy for $(_{_}_BUILD)%%.py.bringup
$(_{_}_BUILD)%%.py.mk: $(_{_})%%.py
	rm -f $@ && ( cd $(_{_}_DIR) && $(PYTHON) $*.py --generic --dep $(__{_}_BUILD)$*.py.mk ) ;\
 [ -e $@ ] || echo "\\$$(_{_}_BUILD)$*.py.bringup:; touch \\$$@" >$@

# Check Python and command line usage examples in .py files
$(_{_}_BUILD)%%.py.tested: $(_{_})%%.py $(_{_}_BUILD)%%.py.mk \\
  $(_{_}_BUILD)style $(_{_}_BUILD)%%.py.bringup $(_{_}_EXE_TESTED)
	( cd $(_{_}_DIR) && $(__{_}_PYTHON) $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$(_{_}_BUILD)%%.sh-test.tested: $(_{_}_BUILD)%%.sh-test $(_{_}_PRETESTED) | \\
  $(_{_}){makemake_py}
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $(_{_}_DIR) && $(PYTHON) {makemake_py} --timeout 60 --sh-test \
	    $(__{_}_BUILD)$*.sh-test ) > $$tmp && mv $$tmp $@
$(_{_}_BUILD)%%.md.sh-test: $(_{_})%%.md | $?/pandoc $?/jq
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
$(_{_})%%.gfm: $(_{_}_BUILD)%%.md
	pandoc --standalone -t $(patsubst .%%,%%,$(suffix $@)) -o $@ $^ \\
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%%an'`"
$(_{_})%%.html $(_{_})%%.pdf $(_{_})%%.dzslides: $(_{_}_BUILD)%%.md | \\
  $?/pandoc $?/xelatex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	pandoc --standalone -t $(patsubst .%%,%%,$(suffix $@)) -o $@ $^ \\
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%%an'`" \\
	       -V min-width=80%%\\!important -V geometry:margin=1in \\
	       --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"

# Make a markdown document.
_{_}_h :=\\n---\\n\\n\\#
_{_}~~~. =\\\\\\footnotesize\\n~~~ {{$1}}
_{_}~~~sh :=$(call _{_}~~~.,.sh)
_{_}~~~ :=~~~\\n\\\\\\normalsize\\n
$(_{_}_BUILD)Makefile.md: $(_{_})Makefile
	( echo "$(_{_}_h)## [$*]($*)" && \\
	  echo "$(call _{_}~~~.,.mk)" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.md: $(_{_})%%
	( echo "$(_{_}_h)## [$*]($*)" && \\
	  echo "$(call _{_}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.md: $(_{_}_BUILD)%%
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \\
	  echo "$(call _{_}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.bringup.md: $(_{_}_BUILD)%%.bringup
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \\
	  echo "$(_{_}~~~sh)" && \\
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%%.tested.md: $(_{_}_BUILD)%%.tested
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \\
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
	git worktree add -d $(_OLD_WORKTREE) $(_{_}_TAG)
endif

# Document last release.
$(_{_})old: $(_{_}_OLD)report.gfm
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BASELINE_INFO)"
$(_{_}_OLD)report.gfm: $(_OLD_WORKTREE)
	( cd $(_{_}_OLD) && $(MAKE) report.gfm --no-print-directory )

# Use GPT for a release review.
$(_{_})%%: $(_{_}_BUILD)%%.diff
	cat $<
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_CHANGES)"
$(_{_}_BUILD)audit.diff: $(_{_}_BUILD)prompt.diff | $(_{_}_PYTHON)
	cat $< > $@
	$(_{_}_PYTHON) -m makemake --prompt $< $(_{_}_MODEL) $(_{_}_TEMPERATURE)\
 $(_{_}_BEARER_rot13) >> $@
$(_{_}_BUILD)prompt.diff: $(_{_}_BUILD)review.diff
	$(PYTHON) $(_{_}){makemake_py} -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $(_{_})review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$(_{_}_BUILD)review.diff: $(_{_}_BUILD)files.diff $(_{_}_BUILD)comments.diff\
  $(_{_}_BUILD)report.diff
	cat $^ > $@
$(_{_}_BUILD)files.diff:
	echo "# $(_{_}_CHANGES_AUDIT)" > $@
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
	      $(PYTHON) $(_{_}){makemake_py} --split $$part '\\n \\n \\n' 's%%02d' && \\
	      sections=`ls s**` && \\
	      changed_sections=`grep -l -e '^-' -e '^+' s**` && \\
	      for section in $$sections ; do \\
	        if `echo "$$changed_sections" | fgrep -wq "$$section" \\
	        || test "$$(wc $$section)" = "1"` ; then \\
	          $(PYTHON) $(_{_}){makemake_py} --split $$section '\\n \\n' 'p%%02d' && \\
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

COMMENT_GROUP_PATTERN = re.compile(r"(\s*#.*)?$")


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
                commands.append(([f"{pip} install {command} --no-warn-script-location"],
                                 [comment], []))

    return commands


def run_command_examples(commands, timeout=3):
    """Run extracted shell commands and verify output"""
    if not commands:
        return

    import subprocess

    # Add PWD to Path so that Windows can run files from there.
    my_env = os.environ.copy()
    my_env["PATH"] = f".{os.pathsep}{my_env['PATH']}"

    for i, (command_lines, comment_lines, output_lines) in enumerate(commands):
        command = "\n".join(map("".join, zip(command_lines, comment_lines)))
        if platform.system() == 'Windows':
            command = f"cmd /C {command}"

        if module_dir:
            command = f"( cd {module_dir} && {command} )"

        output = "\n".join(output_lines)
        result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                timeout=timeout, env=my_env)
        assert not result.returncode, (
            f"Example {i + 1} failed ({result.returncode}): $ {command}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}")

        received = result.stdout or ""
        pattern = '.*'.join(map(re.escape, output.split('...')))
        assert re.fullmatch(pattern, received), (
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
            python = '$(PYTHON)'
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
                     [f"{source} --test > $@"]),
                    (f"{dep_file}: {src_dir}{pattern}.py",
                     [f"{source} --dep $@{generic}"])]
            else:
                rules.append(
                    ((f"{build_dir}{pattern}.py.tested: {src_dir}{pattern}.py"
                      f" {build_dir}{pattern}.py.bringup"),
                     [f"{source} --test > $@"]))

        commands = []
        bringups = build_commands(parent_module.__doc__, '\nDependencies:', embed, end,
                                  pip=f"$(SPEEDUP_WSL_PIP){python} -m pip")
        bringups.append(([f'{python} {source} --shebang'], [''], []))
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


class Shebang(Action):
    """Insert a Windows-compatible shebang, print its PATH configuration if needed, and exit"""

    SHEBANG = '#!venv/python.exe'

    def __call__(self, parser, args, values, option_string=None):
        shebang = None
        src = open(module_path).read()
        if src[:2] == '#!':
            shebang, src = src.split("\n", 1)

        if shebang != self.SHEBANG:
            open(module_path, 'w').write(f'{self.SHEBANG}\n{src}')

        search_path = os.environ['PATH']
        for_windows = '\\' in search_path
        search_dirs = search_path.split(';' if for_windows else ':')
        if '.' not in search_dirs:
            if for_windows:
                print("[System.Environment]::SetEnvironmentVariable('Path',"
                      " '.;' + [System.Environment]::GetEnvironmentVariable('Path', 'User'), 'User')")
            else:
                print("export PATH='.:$PATH'")

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


class Uname(Action):
    """Print the uname parameter and exit"""

    OPTIONS = dict([
        ('-m', '--machine'),
        ('-p', '--processor'),
        ('-s', '--kernel-name'),
    ])

    TRANSLATIONS = dict([
        ('kernel-name', 'system'),
        ('AMD64', 'x86_64')
    ])

    def __call__(self, parser, args, values, option_string=None):
        import platform

        command = self.OPTIONS.get(option_string, option_string)[2:]
        command = self.TRANSLATIONS.get(command, command)
        value = getattr(platform, command)()
        value = self.TRANSLATIONS.get(value, value)
        print(value)
        exit(0)


class GitStatus(Action):
    """List git files wanted git status in a directory, and exit"""

    def __call__(self, parser, args, values, option_string=None):
        import subprocess

        directory, wanted_status = values
        result = subprocess.run(f'git status -s {directory}', shell=True, capture_output=True, text=True)
        assert not result.returncode, result
        for (status, file) in ((row[1], row[3:]) for row in result.stdout.split('\n') if row):
            if status == wanted_status:
                print(file)


class Relpath(Action):
    """Print a relative path and exit"""

    def __call__(self, parser, args, values, option_string=None):
        relative_to = os.path.abspath(values[0])
        for path in values[1:]:
            print(os.path.relpath(os.path.abspath(path), relative_to).replace('\\', '/') + '/')


def add_arguments(argparser):
    argparser.add_argument('--makemake', action='store_true', help=(
        f"Print Makefile for {module_path}, and exit"))
    argparser.add_argument('--generic', action='store_true', help=(
        f"Print generic Makefile for {module_path}, and exit"))
    argparser.add_argument('--dep', action='store', help=(
        f"Build a {module}.dep target, print its Makefile include statement, and exit"))
    argparser.add_argument('--shebang', nargs=0, action=Shebang, help=Shebang.__doc__)
    argparser.add_argument('-c', nargs=1, action=Command, help=Command.__doc__)
    argparser.add_argument('--timeout', type=int, default=10, help=(
        "Test timeout in seconds (10)"))
    argparser.add_argument('--test', nargs=0, action=Test, help=Test.__doc__)
    argparser.add_argument('--sh-test', nargs=1, action=ShTest, help=ShTest.__doc__)


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
    argparser.add_argument('--shebang', nargs=0, action=Shebang, help=Shebang.__doc__)


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=brief(),
        epilog="""Examples:
$ makemake.py --dep build/makemake.dep
include build/makemake.dep

$ cat makemake.dep
build/makemake.py.bringup: makemake.py build/makemake.dep
	$(PYTHON) -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version' > $@"""
               """ && \\
	$(PYTHON) -m pip install requests --no-warn-script-location >> $@ && \\
	$(PYTHON) makemake.py --shebang >> $@ && \\
	chmod +x $< >> $@

$ makemake.py --dep build/makemake.dep --makemake
all: build/makemake.py.tested

build/makemake.py.tested: makemake.py build/makemake.dep build/makemake.py.bringup
	makemake.py --test > $@
build/makemake.dep: makemake.py
	makemake.py --dep $@
include build/makemake.dep

$ makemake.py -c "print(module_py)"
makemake.py

$ makemake.py -m
x86_64

$ makemake.py -s
Windows
""")
    add_arguments(argparser)
    argparser.add_argument('--split', nargs=3, action=Split, help=Split.__doc__)
    argparser.add_argument('--prompt', nargs=4, action=Prompt, help=Prompt.__doc__)
    for brief, long in Uname.OPTIONS.items():
        argparser.add_argument(brief, long, nargs=0, action=Uname, help=Uname.__doc__)
    argparser.add_argument('--git-status', nargs=2, metavar=('directory', 'wanted_status'), default=('.', 'M'),
                           action=GitStatus, help=GitStatus.__doc__)
    argparser.add_argument('--relpath', nargs=2, action=Relpath, help=Relpath.__doc__)
    args = argparser.parse_args()
