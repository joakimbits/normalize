## Generic makefile for co-developed source code and documentation

### Abstract

# Defines generic make targets `bringup tested report review audit clean` for arbitrarily knitted projects.
# Can be included in any other project. Will always make project files in the same location.
# Warns if building recursively rather than being included, but still makes the same.
# Developed on x86 WSL1 and Arm64 MacOSX. Release-tested on GitHub, PowerShell, cmd and Git Bash.

### Usage

# Copy the following five lines into the head of your own Makefile, to make it compliant with this.

    # Prefix all your variable names and project files with this $/ to make your Makefile usable from anywhere.
    Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(Makefile)))))
    $/all: $/bringup

### Avoid using make as a command recipy tool - it is not!

# If $/ *is* used within a recipy, that whole recipy needs to be expanded before the rule is defined, like this:

    define META
        $/meta-recipy:
	        # $$@: $$^ - Every $$ except the $$/ in the recipy needs to be doubled now!
	        echo "Like this: $$$$$$$$PATH = $$$$PATH"
	        # And the recipy itself needs to be be defined by`$$(eval ...)`-ing it first.
            # This recipy will execute every `make meta-recipy` since $$@ is never done by it.
    endef
    $(eval $(META))

    $/normal-target: $/this-is-much-better
	    # $@: $^ - This rule expansion from $$/ is available in recipy variables $$@: $$^.
	    touch $@
	    # This recipy will not execute again unless an update is actually needed, because $$/normal-target *was touched*.
    $/this-is-much-better: ; touch $@

    .PHONY: $/normal-target # This is how to force the recipy to re-execute every `make` where $/normal-target is needed.
    # Another way is to have a .PHONY target as a dependency after `:`, before any `|`.
    # A third (recommended) way is to not create and update the target in its recipy.

### How to make make know both what to make, when, using what, and how

# The whole purpose of `make` is to avoid remaking things done right, and always do everything right.
# For that to work, we need *all* dependencies listed, either directly or indirectly, after the `:`.
# If a target does have dependencies with irrelevant timestamp, place them after a `|`.
# If a target does have dependencies on specific timestamps or versions - or anything else within some dependencies -
# create an intermediate target to depend on instead. A `touch $@` within its recipy gives `make` its proper timestamp.

#### Bring-up project

# `make`, `make all`: Bring-up all executables from all source code in all projects here.
# All commands needed for that to happen on your system is printed, and these depend on the state of your system.
# If nothing changed since last `make`, no commands are needed, and nothing is therefore printed. It is normal.

#### Tear-down project

# `make clean`: Remove everything built locally by the project. Normally done by IDEs when switching branches.
# Note: System changes made outside the project directory (see below) are not undone.

#### System changes

# `make`: `.` becomes first directory on the current user's PATH - if there is at least one .py file in a project here.
# `make pdf html slides`: Installs latex and fonts.

#### Self-tests

# `make report`: The following tests are performed, in this order, without any tear-down in-between.

#   1. The binary executable is tested: Not failing to execute with an empty file as stdin.
#   2. All usage examples in .py files are verified to match exactly. Command line usage examples also.
#   3. All sh blocks in .md files (command line usage examples) are verified to match exactly.

# Even if only a single character in a self-test does not match, it blocks progress for anything after it.
# This means that every usage examples can safely assume that everything above exists already and passed their tests.

#### Documentation

# `gfm pdf html slides`: Print links to reports documenting all details of the project, including its *.md files.
# The `--help` usage information for each executable is included.
# Any examples in `--help` matched exactly what the executable did when tested in its project directory.

#### Review

# `old changes review audit`: Compare the project with last release.
# Changes are very brief, as part of an otherwise collapsed complete source code tree.
# Audit is done with help of openai, using GPT-3.5-turbo by default.
# Configure your own openai account in your maker if you need a larger context - see Parameters below.

#### Recommended dependencies

# `build/*.py.bringup`: *.py is executable using a venv/bin/python next to it.
# `build/directory-name.bringup`: ./directory-name is executable as-is.
# `build/*.tested`: * is self-tested without failure, and the test output is here.
# `build/*.md`: * is documented here.

#### Binary executable

# A single binary executable is made for any assembly code or compilable code found locally here.
# Assembly source code is assumed to have instructions on the project computer and contain a _start entry.
# Compilable code is assumed to contain a single main() function.

# In a Makefile:

    $/example.txt: $/example/example; $< > $@
    $/tested-example.txt: $/example/example $/example/build/example.tested; $< > $@

# In a shell:
$/binary_executable_shell_example:

	make && ( cd example && ./example ) > example.txt
	make tested && ( cd example && ./example ) > tested-example.txt

#### Python executables and modules

# A single Python venv is made for .py code found *here*, but subprojects gets their own unique venv.
# Python code is assumed to import makemake and will then get a Shebang that works *here* only.

# In a Makefile:

    $/greeter.txt: $/example/bin/python $/example/greeter.py $/example/build/greeter.py.bringup; $(wordlist 1,2,$^) > $@
    $/tested-greeter.txt: $/example/bin/python $/example/greeter.py $/example/build/greeter.py.tested; $(wordlist 1,2,$^) > $@

# In a shell:
$/python_executable_shell_example:

	make && ( cd example && greeter.py ) > greeter-from-shell.txt
	make tested && ( cd example && greeter.py ) > tested-greeter-from-shell.txt

# In Python:

#   * Copy its `Dependencies:` into your own .py header.
#   * `touch __main__.py` on the complete path to it. Now you can import and use it.

	touch example/__main__.py
	venv/bin/python -c "import example; open('greeter-from-py.txt).write(example.greeter.hello())"


## How it works

# All project variable names here except a special $/ "here prefix" are always unique globally.
# This is achieved by using $/ as prefix in the *name* of each project-unique variable.
# Any subdirectory with at least one documentation file (.md suffix) is detected as a subproject.
# A link to this Makefile is created in all those subdirectories, and by them further into all project leaves.
# Every $/ here is expanded before these subproject Makefiles are included, so their $/ is theirs only.
# The main subproject targets are nested as dependencies to corresponding targets here.
# The innermost projects therefore gets made first.

### Daughter project dependencies

# If you #include daughter .h files in your source code, or have daughter Dependencies in your .py header, all is fine.
# You may need to create links to sibling source code or sibling documentation needed here though.

### Sibling project dependencies

# If you #include sibling .h files in your source code, or have sibling Dependencies in your .py header, all is fine
# as long as you build from the parent project level or `make DEPS=../sibling/Makefile` from here.
# You may need to create links to sibling source code or sibling documentation needed here though.

# You could also consider making this the parent project instead, or creating a customized Makefile here like below
# (as if it was already a parent project) but without `$/NON-SUBPROJECTS`.

### Parent project dependencies

# Replace the parent generic Makefile with the following customized one and then treat the parent as a sibling
# project like above.

    # Prefix all your variable names and project files with this $/ to make your Makefile usable from anywhere.
    _Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(_Makefile)))))

    ifneq (clean,$(findstring clean,$(MAKECMDGOALS)))
        $/project.mk:
	        curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/Makefile -o $@
    endif

    $/NON-SUBPROJECTS += $/this
    #$/DEPS += $/this/Makefile
    #-include $/project.mk

# Replace `#$/DEPS += $/this-project/Makefile` with this Makefile, and activate the last line `-include $/project.mk`.
# Then this project is no longer built and reported together with the parent project, but the parent project can still
# build everything here on a per-need basis.

# To build the parent project from here, `make DEPS=../Makefile` or consider making also this a custom Makefile with
# `$/DEPS += $/../Makefile` (and no `$/NON-SUBPROJECTS`).

# You could also consider making this a sibling project to the parent project instead.


## Parameters

# Configure a GPT model to use for `audit`
#  - A large-context openai model suitable for code review
#  - A rot13 encoded openai Bearer key for its GPT session.
#  - A temperature for its openai continuation.
GPT_MODEL ?= gpt-3.5-turbo-16k
GPT_BEARER_rot13 ?= fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj
GPT_TEMPERATURE ?= 0.7

# Where to make files
_$/BUILD ?= build/
$/BUILD :=$/$(_$/BUILD)

# The maker's home directory and name
~ := $(shell echo ~)
I := $(shell whoami)

# Workaround Windows feature: Windows domain in whoami
I := $(subst \, ,$I)
ifneq ($(words $I),1)
    DOMAIN := $(firstword $(WHOAMI))
    I := $(lastword $I)
endif

# Workaround Windows WSL1 bug: Recursive make shell believes it is git bash on Windows
ifeq ($~,/Users/$I)
    ~ := /home/$I
endif

# A base PYTHON to use. It can be one of:
#  - `python3` on Ubuntu or Mac,
#  - `python.exe` in Windows from WSL Ubuntu, or
#  - `python` on Windows.
#  - or any given PYTHON.
ifeq ($~,/home/$I)
    PYTHON ?= python3
    VENV_PYTHON ?= bin/python

    # Workaround Windows WSL bridge bug: Timeout on ipv6 internet routes - slows down pip.
    ifneq ($(shell echo $$WSL_DISTRO_NAME),)
        SPEEDUP_WSL_DNS ?= $~/use_windows_dns.sh $?/pip
        SPEEDUP_WSL_PIP ?= DISPLAY= #
    endif
else
    PYTHON ?= python
    VENV_PYTHON ?= python.exe
endif
override PYTHON := $(shell which $(PYTHON))
$/PROJECT_PYTHON := $/venv/$(VENV_PYTHON)

# A package manager for the PYTHON OS
ifndef !
    UNAME ?= $(PYTHON) $/makemake.py
    CPU ?= $(shell $(UNAME) -m)
    OS ?= $(shell $(UNAME) -s)
    ifeq (MacOSX,$(OS))
        ! ?= brew install
        ? ?= /opt/homebrew/bin
        FONTS ?= ~/Library/Fonts
        COUSINE := $(FONTS)
        CARLITO := $(FONTS)
    else
        ! ?= sudo apt update && sudo apt install -y
        ? ?= /usr/bin
        COUSINE ?= /usr/share/fonts/truetype/cousine
        CARLITO ?= /usr/share/fonts/truetype/crosextra
    endif
endif


### Variables

#### Define the rest here only once

ifndef $/PROJECT
ifeq (,$/)
    $/PROJECT := ./
else
    $/PROJECT := $/
endif
$/NAME := $(notdir $(realpath $($/PROJECT)))

#### Find subdirectories containing at least one .md file

$/NON-SUBPROJECTS += $($/BUILD)
$/SUBDIRS := $(foreach d,$(shell find $/. -mindepth 1 -maxdepth 1),$(notdir $d))
$/SUBPROJECTS += $(sort $(dir $(foreach d,$($/SUBDIRS),$(wildcard $/$d/*.md))))
$/SUBPROJECTS := $(filter-out $($/NON-SUBPROJECTS),$($/SUBPROJECTS))
$/ACTIVE_SUBPROJECTS := $(dir $(foreach d,$($/SUBPROJECTS),$(wildcard $/$dMakefile)))

#### Make sub-projects before this project

$/all: | $($/ACTIVE_SUBPROJECTS:%=%all)
$/tested: | $($/ACTIVE_SUBPROJECTS:%=%tested)
$/report: | $($/ACTIVE_SUBPROJECTS:%=%report)
$/gfm: | $($/ACTIVE_SUBPROJECTS:%=%gfm)
$/pdf: | $($/ACTIVE_SUBPROJECTS:%=%pdf)
$/html: | $($/ACTIVE_SUBPROJECTS:%=%html)
$/slides: | $($/ACTIVE_SUBPROJECTS:%=%slides)
$/old: | $($/ACTIVE_SUBPROJECTS:%=%old)
$/new: $($/ACTIVE_SUBPROJECTS:%=%new)
$/build/review.diff: $($/ACTIVE_SUBPROJECTS:%=%build/review.diff)

#### Remove all built files in all projects
define META
    $/clean: | $($/ACTIVE_SUBPROJECTS:%=%clean)
	    rm -rf $/build/ $/venv/ $/.ruff_cache/
endef
$(eval $(META))

#### Define targets, rules and recipies, but only when actually building

ifneq (clean,$(findstring clean,$(MAKECMDGOALS)))

# Make local commands available
PATHS := $(subst ;, ,$(subst :, ,$(PATH)))
ifeq (,$(filter .,$(PATHS)))
    .-ON-PATH := .-on-$(OS)-path
endif

# Setup this Makefile in each subproject

$/%/Makefile: | $/Makefile $/%/makemake.py
	ln -s ../Makefile $@
$/%/makemake.py: | $/makemake.py
	ln -s ../makemake.py $@
$/makemake.py:
	curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/makemake.py -o $@
.PRECIOUS: $/makemake.py $($/SUBPROJECTS:%=%makemake.py)

# Notify the user if new rules were built and included, and make therefore restarted
ifeq (2,$(MAKE_RESTARTS))
    ifndef MAKER
        $(info # Hello $I, Welcome to makemake https://github.com/joakimbits/normalize)
    endif

    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $($/BUILD)
    $(info # $(PWD) $(filter-out $(INCLUDING)%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $/makemake.py $($/PROJECT_PYTHON) $($/BUILD))
    INCLUDED := $(MAKEFILE_LIST)
    INCLUDING := $($/BUILD)

    # Notify the user on abusage of make
    ifneq (0,$(MAKELEVEL))
        $(info # Warning: This is a recursive $(MAKE). Please use global variable names and include instead.)
        $(info # https://aegis.sourceforge.net/auug97.pdf)
        $(info # https://github.com/joakimbits/normalize/blob/main/example/Makefile)
    endif
endif

# Find all source files
$/SOURCE :=
$/MAKEFILE := $(shell find $/Makefile \! -type l 2>/dev/null)
$/SOURCE += $($/MAKEFILE)
$/S := $(shell find $/*.s \! -type l 2>/dev/null)
$/SOURCE += $($/S)
$/C := $(shell find $/*.c \! -type l 2>/dev/null)
$/SOURCE += $($/C)
$/H := $(shell find $/*.h \! -type l 2>/dev/null)
$/SOURCE += $($/H)
$/CPP := $(shell find $/*.cpp \! -type l 2>/dev/null)
$/SOURCE += $($/CPP)
$/HPP := $(shell find $/*.hpp \! -type l 2>/dev/null)
$/SOURCE += $($/HPP)
$/PY := $(shell find $/*.py \! -type l 2>/dev/null)
$/PY := $(subst ./,$/,$($/PY))
$/SOURCE += $($/PY)
$/MD := $(shell find $/*.md \! -type l 2>/dev/null)
$/SOURCE += $($/MD)

# Find our git status
$/BRANCH := $(shell git branch --show-current)
$/BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
$/KNOWN := $(addprefix$/,$(shell cd $($/PROJECT) ; git ls-files . ':!:*/*'))
$/ADD := $(filter-out $($/KNOWN),$($/SOURCE))
$/MODIFIED := $(shell cd $($/PROJECT) && $(PYTHON) makemake.py --git-status . M)
$/REMOVE := $(filter-out $($/SOURCE),$($/KNOWN))

# Figure out where to checkout an old worktree
$/HOME_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/HOME := $($/HOME_DIR:./%=%)
$/HOME_NAME := $(notdir $(abspath $($/HOME_DIR)))
$/GIT_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/HERE_DIR := $(shell $(PYTHON) $/makemake.py --relpath $($/GIT_DIR) $($/PROJECT))/
$/HERE := $($/HERE_DIR:%./=%)
$/OLD_WORKTREE := $($/HOME)$(_$/BUILD)$($/BASELINE)/$($/HOME_NAME)/
$/OLD := $($/OLD_WORKTREE)$($/HERE)

## Colorize edited files by their git status
NORMAL ?= `tput sgr0`
RED ?= `tput setaf 1`
GREEN ?= `tput setaf 2`
YELLOW ?= `tput setaf 3`
BLUE ?= `tput setaf 4`
REVERSED ?= `tput rev`
$/BRANCH_STATUS := $(if $($/ADD),$(RED)$($/ADD)$(NORMAL))
$/BRANCH_STATUS += $(if $($/MODIFIED),$(BLUE)$($/MODIFIED)$(NORMAL))
$/BRANCH_STATUS += $(if $($/REMOVE),$(REVERSED)$($/REMOVE)$(NORMAL))
$/COMMIT_INFO := $(shell git log -1 --oneline $($/PROJECT))
$/BRANCH_STATUS += $($/COMMIT_INFO)

ifeq ($(filter v%,$($/BASELINE)),)
    $/BASELINE_INFO := $(shell git show --oneline -s $($/BASELINE))
else
    $/BASELINE_INFO := $(strip $(shell git tag --list $($/BASELINE) -n1))
endif

$/CHANGES := $($/BASELINE_INFO) --> $($/BRANCH_STATUS)
$/CHANGES_AUDIT := $($/BASELINE_INFO) -->
$/CHANGES_AUDIT += $($/ADD)
$/CHANGES_AUDIT += $($/MODIFIED)
$/CHANGES_AUDIT += $($/COMMIT_INFO)

# Collect code
$/LINKABLE := $($/S)
$/COMPILABLE := $($/C)
$/COMPILABLE += $($/CPP)
$/LINKABLE += $($/COMPILABLE)
$/CODE := $($/SRCS)
$/CODE += $($/PY)

## Prepare for compilation
$/INC_DIRS := $($/PROJECT)
$/LDFLAGS := $(LDFLAGS)

# A linked executable has the same name as the project
ifneq (,$(strip $($/LINKABLE)))
    $/EXE := $/$($/NAME)
    $/EXE_TESTED := $($/BUILD)$($/NAME).tested
endif

# If we got assembly source, assume it has _start code
ifneq ($(strip $($/S)),)
    $/LDFLAGS += -nostartfiles -no-pie
endif

$/CXXFLAGS := $($/LDFLAGS)
$/CXXFLAGS += -S $(addprefix -I,$($/INC_DIRS)) -MMD -MP
$/CFLAGS := $($/CXXFLAGS)
$/CXXFLAGS += $(CXXFLAGS)
$/CFLAGS += $(CFLAGS)
$/COBJS := $($/COMPILABLE:$/%=$($/BUILD)%.s)
$/DEPS += $($/COBJS:.s=.d)
$/OBJS := $($/S)
$/OBJS += $($/COBJS)
$/EXES := $($/EXE)
$/EXES += $($/PY)

# Collect bringup and tested targets
$/BRINGUP := $($/PY:$/%=$($/BUILD)%.bringup)
$/TESTED += $($/PY:$/%=$($/BUILD)%.tested)
$/PRETESTED := $($/TESTED)
$/TESTED += $($/MD:$/%=$($/BUILD)%.sh-test.tested)

# Prepare for bringup
$/PY_MK := $($/PY:$/%=$($/BUILD)%.mk)
$/DEPS += $($/PY_MK)

# Prepare for reporting
$/LOGIC := $($/MAKEFILE)
$/LOGIC += $($/CODE)
$/RESULT := $($/PY_MK)
$/RESULT += $($/BRINGUP)
$/RESULT += $($/TESTED)
$/REPORT := $($/BUILD)report-details.md
$/REPORT += $($/LOGIC:$/%=$($/BUILD)%.md)
$/REPORT += $($/RESULT:%=%.md)

## Targets

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Do not use any built-in rules
.SUFFIXES:

# Convenience targets
.PHONY: $/bringup $/tested $/clean
$/bringup: $($/EXE) $($/BRINGUP)
$/tested: $($/TESTED)

ifneq (,$($/OBJS))
define META
    # build/*.c.s: Compile C
    $($/BUILD)%.c.s: $/%.c
	    $(CXX) $($/CFLAGS) -c $$< -o $$@

    # build/*.cpp.s: Compile C++
    $($/BUILD)%.cpp.s: $/%.cpp
	    $(CXX) $($/CXXFLAGS) -c $$< -o $$@

    # Link executable
    $/$($/NAME): $($/OBJS)
	    # $$@: $$^
	    $(CC) $($/LDFLAGS) $$^ -o $$@

    # Test executable:
    $($/BUILD)$($/NAME).tested: $/$($/NAME)
	    true | ./$$< > $$@ || (cat $$@ && false)
endef
$(eval $(META))
endif

# Check Python 3.9 syntax
$/syntax: $($/BUILD)syntax
$($/BUILD)%.py.syntax: $($/PROJECT_PYTHON) $/%.py | $/venv/lib/python/site-packages/ruff
	$< -m ruff --select=E9,F63,F7,F82 --target-version=py39 $(lastword,$^) > $@ || (cat $@ && false)

# Install pip package in the local python:
$/venv/lib/python/site-packages/%: $($/PROJECT_PYTHON) $/venv/lib/python/site-packages
	 $< -m pip install $*

# Link to actual site-packages
$/venv/lib/python/site-packages: $($/PROJECT_PYTHON)
	mkdir -p $(dir $@)
	ln -s $$(realpath --relative-to=$(dir $@) `$< -c "import sys; print(sys.path[-1])"`) $@

# Workaround Windows python not installing #!venv/bin/python
ifeq ($(PYTHON),/mnt/c/tools/miniconda3/python.exe)
    $/PYTHON_FINALIZE ?= && mkdir -p $(dir $@) && ln -s ../Scripts/python.exe $@
endif

# Setup a local shebang python:
$/venv/bin/python: | $(PYTHON) $(.-ON-PATH) $(SPEEDUP_WSL_DNS)
	( cd $(patsubst %venv/bin/python,%.,$@) && $(SPEEDUP_WSL_PIP)$(PYTHON) -m venv venv ) $($/PYTHON_FINALIZE)
	$(SPEEDUP_WSL_PIP)$@ -m pip install --upgrade pip
	$(SPEEDUP_WSL_PIP)$@ -m pip install requests  # Needed by -m makemake --prompt

# Install local commands before other commands
ifndef .-ON-PATH_TARGETS
    .-ON-PATH_TARGETS = 1
    %-on-Linux-path: ~/.profile
	    echo 'export PATH="$*:$$PATH"' >> $<
	    false # Please `source $<` or open a new shell to get $* on PATH, and retry `make $(MAKECMDGOALS)`.
    %-on-MacOSX-path: ~/.zshrc
	    echo 'export PATH="$*:$$PATH"' >> $<
	    false # Please `source $<` or open a new shell to get $* on PATH, and retry `make $(MAKECMDGOALS)`.
    %-on-Windows-path:
	    $(call ps1,[System.Environment]::SetEnvironmentVariable('Path', '$*;' + [System.Environment]::GetEnvironmentVariable('Path', 'User'), 'User'))
endif

ifndef SPEEDUP_WSL_DNS_TARGET
    SPEEDUP_WSL_DNS_TARGET = 1
    $~/use_windows_dns.sh:
	    echo "# Fixing DNS issue in WSL https://gist.github.com/ThePlenkov/6ecf2a43e2b3898e8cd4986d277b5ecf#file-boot-sh" > $@
	    echo -n "sed -i '/nameserver/d' /etc/resolv.conf && " >> $@
	    echo -n  "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command " >> $@
	    echo -n   "'(Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses | " >> $@
	    echo -n    "ForEach-Object { \"nameserver \$$_\" }' | tr -d '\\r' | " >> $@
	    echo "tee -a /etc/resolv.conf > /dev/null" >> $@
	    sudo sed -i '\|command=$@|d' /etc/wsl.conf
	    echo "command=$@" | sudo tee -a /etc/wsl.conf > /dev/null
	    sudo sh $@
endif

ifndef INSTALL_PIP_TARGET
    INSTALL_PIP_TARGET = 1
    $?/pip:
	    $! python3.10-pip
endif

# Check Python 3.9 style
$($/BUILD)%.py.style: $/%.py $($/BUILD)%.py.syntax $($/PROJECT_PYTHON)
	$(word 3,$^) -m ruff --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Build a recipy for $($/BUILD)%.py.bringup
$($/BUILD)%.py.mk: $/. $/%.py
	rm -f $@ && ( cd $< && $(PYTHON) $*.py --generic --dep $(patsubst $(dir $<)%,%,$@) ) ; [ -e $@ ] || echo "\$$(_$$/BUILD)$*.py.bringup:; touch \$$@" > $@

# Check Python and command line usage examples in .py files
$($/BUILD)%.py.tested: $/. $/%.py $($/BUILD)%.py.mk $($/BUILD)%.py.style $($/BUILD)%.py.bringup $($/EXE_TESTED) | $($/PROJECT_PYTHON)
	( cd $< && $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$($/BUILD)%.sh-test.tested: $($/PROJECT) $($/PRETESTED) $($/BUILD)%.sh-test | $/makemake.py
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $< && $(PYTHON) makemake.py --timeout 60 --sh-test $(patsubst $(dir $<)%,%,$(lastword $^)) ) > $$tmp && mv $$tmp $@
$($($/BUILD)%.md.sh-test: $/%.md | $?/pandoc $?/jq)
$($/BUILD)%.md.sh-test: $/%.md | $?/pandoc $?/jq
	pandoc -i $< -t json --preserve-tabs | jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && truncate -s -1 $@

# Document all source codes:
$/s: $($/SOURCE)
	@$(foreach s,$^,echo "___ $(s): ____" && cat $(s) ; )

# Document all assembly codes linked into $/$($/NAME).
$/a: $($/OBJS)
	@$(foreach a,$^,echo "___ $(a): ____" && cat $(a) ; )

# Document all dependencies.
$/d: $($/DEPS)
	@$(foreach d,$^,echo "___ $(d): ____" && cat $(d) ; )

# Document all bringups.
$/b: $($/BRINGUP)
	@$(foreach b,$^,echo "___ $(b) ____" && cat $(b) ; )

# Document all test results.
$/report: $($/BUILD)report.txt
	@cat $<
$($/BUILD)report.txt: $($/TESTED)
	( $(foreach t,$^,echo "___ $(t): ____" && cat $(t) ; ) ) > $@

# Make a standalone html, pdf, gfm or dzslides document.
define META
    $/%.gfm: $($/BUILD)%.md
	pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	       -M title="$($/NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`"
    $/%.html $/%.pdf $/%.dzslides: $($/BUILD)%.md | \
      $?/pandoc $?/xelatex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	    pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	           -M title="$$($/NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`" \
	           -V min-width=80%\!important -V geometry:margin=1in \
	           --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"
endef
$(eval $(META))

# Make a markdown document.
$/h := \n---\n\n\#
$/~~~. = \\footnotesize\n~~~ {$1}
$/~~~sh := $(call $/~~~.,.sh)
$/~~~ := ~~~\n\\normalsize\n
define META
    $($/BUILD)Makefile.md: project.mk
	    ( echo "$($/h)## [$$*]($$*)" && \
	      echo "$(call $/~~~.,.mk)" && \
	      cat $$< && echo "$($/~~~)" ) > $$@
    $($/BUILD)%.md: $/%
	    ( echo "$($/h)## [$$*]($$*)" && \
	      echo "$(call $/~~~.,$$(suffix $$<))" && \
	      cat $$< && echo "$($/~~~)" ) > $@
    $($/BUILD)%.md: $($/BUILD)%
	    ( echo "$($/h)## [$$*]($(_$/BUILD)$$*)" && \
	      echo "$(call $/~~~.,$$(suffix $$<))" && \
	      cat $$< && echo "$($/~~~)" ) > $$@
    $($/BUILD)%.bringup.md: $($/BUILD)%.bringup
	    ( echo "$($/h)## [$$*]($(_$/BUILD)$$*)" && \
	      echo "$($/~~~sh)" && \
	      cat $$< && echo "$($/~~~)" ) > $$@
    $($/BUILD)%.tested.md: $($/BUILD)%.tested
	    ( echo "$($/h)## [$$*]($(_$/BUILD)$$*)" && \
	      echo "$($/~~~sh)" && \
	      cat $$< && echo "$($/~~~)" ) > $$@
endef
$(eval $(META))

# Report the project.
define META
    $/%: $/report.%
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $($/BRANCH_STATUS)"
    $/slides: $/slides.html
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $($/BRANCH_STATUS)"
endef
$(eval $(META))
$/slides.html: $/report.dzslides
	mv $< $@
$/report.html $/report.pdf $/report.gfm $/report.dzslides: $($/MD) $($/REPORT)
$/file = $(foreach _,$1,[\`$_\`]($_))
$/exe = $(foreach _,$1,[\`$_\`]($_))
$/h_fixup := sed -E '/^$$|[.]{3}/d'
#define META
    $($/BUILD)report.md: $($/BUILD)report.txt
	    echo "A build-here include-from-anywhere project based on [makemake](https://github.com/joakimbits/normalize)." > $$@
	    echo "\n- \`make report pdf html slides review audit\`" >> $$@
    ifneq (,$(strip $($/EXE)))
	    echo "- \`./$($/NAME)\`: $(subst $/,,$(call $/file,$($/SRCS)))" >> $$@
    endif
    ifneq (,$(strip $($/PY)))
	    echo "- $(subst $/,,$(call $/exe,$($/PY)))" >> $@
    endif
	    echo "$($/h)## Installation" >> $@
	    echo "$($/~~~sh)" >> $@
	    echo "\$$ make" >> $@
	    echo "$($/~~~)" >> $@
    ifneq (,$(strip $($/EXE)))
	    echo "- Installs \`./$($/NAME)\`." >> $$@
    endif
    ifneq (,$(strip $($/PY)))
	    echo "- Installs \`./venv\`." >> $$@
	    echo "- Installs $(subst $/,,$(call $/exe,$($/PY)))." >> $$@
    endif
    ifneq (,$($/EXES))
	    echo "$($/h)## Usage" >> $$@
	    echo "$($/~~~sh)" >> $$@
	    for x in $(subst $($/PROJECT),,$($/EXES)) ; do \
	      echo "\$$$$ true | ./$$$$x -h | $($/h_fixup)" >> $$@ && \
	      ( cd $($/PROJECT) && true | ./$$$$x -h ) > $$@.tmp && \
	      $($/h_fixup) $$@.tmp >> $$@ && rm $$@.tmp ; \
	    done
	    echo >> $$@
	    echo "$($/~~~)" >> $$@
	    echo "$($/h)## Test" >> $$@
	    echo "$($/~~~sh)" >> $$@
	    echo "\$$$$ make tested" >> $$@
	    echo "$($/~~~)" >> $$@
    endif
    ifneq (,$(strip $($/EXE)))
	    echo "- Tests \`./$($/NAME)\`." >> $$@
    endif
    ifneq (,$(strip $($/PY)))
	    echo "- Verifies style and doctests in $(subst $($/PROJECT),,$(call $/file,$($/PY)))." >> $$@
    endif
    ifneq (,$(strip $($/MD)))
	     echo "- Verifies doctests in $(subst $($/PROJECT),,$(call $/file,$($/MD)))." >> $$@
    endif
    ifneq (,$(strip $($/CODE)))
	    echo "$($/h)## Result" >> $$@
	    echo "$($/~~~sh)" >> $$@
	    echo "\$$$$ make report" >> $$@
	    ( cd $($/PROJECT) && $(MAKE) report --no-print-directory ) >> $$@
	    echo "$($/~~~)" >> $$@
	    echo "\n---\n" >> $$@
    endif
#endef
#$(info $(META))
#$(eval $(META))
$($/BUILD)report-details.md:
	echo "$($/h)# Source code, installation and test result" >> $@

# Build an old worktree that is shared by all projects in this git
ifndef _OLD_WORKTREE
    _OLD_WORKTREE := $($/OLD_WORKTREE)
    $(_OLD_WORKTREE):
	    git worktree add -d $(_OLD_WORKTREE) $($/TAG)
endif

# Document last release.
$/old: $($/OLD)report.gfm
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/BASELINE_INFO)"
$($/OLD)report.gfm: $(_OLD_WORKTREE)
	( cd $($/OLD) && $(MAKE) report.gfm --no-print-directory )

# Use GPT for a release review.
$/%: $($/BUILD)%.diff
	cat $<
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/CHANGES)"
define META
    $($/BUILD)audit.diff: $($/BUILD)prompt.diff | $($/PROJECT_PYTHON)
	    cat $$< > $$@
	    $($/PROJECT_PYTHON) -m makemake --prompt $$< $(GPT_MODEL) $(GPT_TEMPERATURE) $(GPT_BEARER_rot13) >> $$@
endef
$(eval $(META))
$($/BUILD)prompt.diff: $($/BUILD)review.diff
	$(PYTHON) $/makemake.py -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $/review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$($/BUILD)review.diff: $($/BUILD)files.diff $($/BUILD)comments.diff $($/BUILD)report.diff
	cat $^ > $@
$($/BUILD)files.diff:
	echo "# $($/CHANGES_AUDIT)" > $@
define META
    $($/BUILD)comments.diff:
	    echo "git --no-pager log --no-merges $($/BASELINE)..HEAD $($/PROJECT)" > $$@
	    git --no-pager log --no-merges $($/BASELINE)..HEAD $($/PROJECT) >> $$@
endef
$(eval $(META))
$($/BUILD)report.diff: $($/OLD)report.gfm $/report.gfm $/makemake.py
	echo "diff -u -U 100000 $< $(word 2,$^) | fold-unchanged" > $@
	( diff -u -U 100000 $< $(word 2,$^) | csplit -s - /----/ '{*}' && \
	  parts=`ls xx**` && \
	  changed_parts=`grep -l -e '^-' -e '^+' xx**` && \
	  for part in $$parts ; do \
	    if `echo "$$changed_parts" | fgrep -wq "$$part" \
	    || test "$$(wc $$part)" = "1"` ; then \
	      $(PYTHON) $(word 3,$^) --split $$part '\n \n \n' 's%02d' && \
	      sections=`ls s**` && \
	      changed_sections=`grep -l -e '^-' -e '^+' s**` && \
	      for section in $$sections ; do \
	        if `echo "$$changed_sections" | fgrep -wq "$$section" \
	        || test "$$(wc $$section)" = "1"` ; then \
	          $(PYTHON) $(word 3,$^) --split $$section '\n \n' 'p%02d' && \
	          paragraphs=`ls p**` && \
	          changed_paragraphs=`grep -l -e '^-' -e '^+' p**` && \
	          for paragraph in $$paragraphs ; do \
	            if `echo "$$changed_paragraphs" | fgrep -wq "$$paragraph"` ; then \
	              cat $$paragraph ; echo ; echo ; \
	            else \
	              echo "$$(head -1 $$paragraph) ..." ; fi ; \
	            done ; \
	          rm p** ; \
	        else \
	          echo "$$(head -1 $$section) ..." ; fi ; \
	        done ; \
	      rm s** ; \
	    else \
	      echo "$$(sed -n '3p' $$part) ..." ; fi ; \
	    done ; \
	  rm xx**; ) >> $@
endif # building

## Finally attempt to include all bringup files and sub-projects
# Note: Subprojects modify $/, so this has to be the last command using it as a prefix here.
$/DEPS += $($/SUBPROJECTS:%=%Makefile)
$/DEPS := $(filter-out $($/NON-DEPS),$($/DEPS))
-include $($/DEPS)

endif # first time
