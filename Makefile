## Generic makefile for co-developed source code and documentation

### Abstract

# Defines generic make targets `bringup tested report review audit clean` for arbitrarily knitted projects.
# Can be included in any other project. Will always make project files in the same location.
# Warns if building recursively rather than being included, but still makes the same.
# Developed on x86 WSL1 and Arm64 MacOSX. Release-tested on GitHub, PowerShell, cmd and Git Bash.

### Usage

# Copy the following five lines into the head of your own Makefile, to make it compliant with this.

    # Prefixing variable names with $/_ and project files with $/ to make this Makefile usable from anywhere.
    Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst ./%,%,$(subst \,/,$(subst C:\,/c/,$(dir $(Makefile)))))
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

# `build/*.py.bringup`: *.py is executable using a venv/bin/python3 next to it.
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

    $/greeter.txt: $/example/bin/python3 $/example/greeter.py $/example/build/greeter.py.bringup; $(wordlist 1,2,$^) > $@
    $/tested-greeter.txt: $/example/bin/python3 $/example/greeter.py $/example/build/greeter.py.tested; $(wordlist 1,2,$^) > $@

# In a shell:
$/python_executable_shell_example:

	make && ( cd example && greeter.py ) > greeter-from-shell.txt
	make tested && ( cd example && greeter.py ) > tested-greeter-from-shell.txt

# In Python:

#   * Copy its `Dependencies:` into your own .py header.
#   * `touch __main__.py` on the complete path to it. Now you can import and use it.

	touch example/__main__.py
	venv/bin/python3 -c "import example; open('greeter-from-py.txt).write(example.greeter.hello())"


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
# (as if it was already a parent project) but without `$/_NON-SUBPROJECTS`.

### Parent project dependencies

# Replace the parent generic Makefile with the following customized one and then treat the parent as a sibling
# project like above.

    # Prefixing variable names with $/_ and project files with $/ to make this Makefile usable from anywhere.
    _Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst ./%,%,$(subst \,/,$(patsubst C:\%,/c/%,$(dir $(Makefile)))))

    ifneq (clean,$(findstring clean,$(MAKECMDGOALS)))
        $/project.mk:
	        curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/Makefile -o $@
    endif

    $/_NON-SUBPROJECTS += $/this
    # $/_DEPS += $/this/Makefile
    #-include $/project.mk

# Replace `# $/_DEPS += $/this-project/Makefile` with this Makefile, and activate the last line `-include $/project.mk`.
# Then this project is no longer built and reported together with the parent project, but the parent project can still
# build everything here on a per-need basis.

# To build the parent project from here, `make DEPS=../Makefile` or consider making also this a custom Makefile with
# `$/_DEPS += $/../Makefile` (and no `$/_NON-SUBPROJECTS`).

# You could also consider making this a sibling project to the parent project instead.


## Parameters

# Configure a GPT model to use for `audit`
#  - A large-context openai model suitable for code review
#  - A rot13 encoded openai Bearer key for its GPT session.
#  - A temperature for its openai continuation.
GPT_MODEL ?= gpt-3.5-turbo-16k
GPT_BEARER_rot13 ?= fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj
GPT_TEMPERATURE ?= 0.7

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
    VENV_PYTHON ?= bin/python3

    ifneq ($(shell echo $$WSL_DISTRO_NAME),)
    	# Clone Windows home git and ssh settings
        ifndef H
            H := $(shell wslpath `cmd.exe /C echo %USERPROFILE% | head -c -2`)
            ~/.gitconfig: $H/.gitconfig
	            cp $< $@
            ~/.ssh: $H/.ssh
	            cp -r $< $(dir $@)
        endif

        # Workaround Windows WSL bridge bug: Timeout on ipv6 internet routes - slows down pip.
        SPEEDUP_WSL_DNS ?= $~/use_windows_dns.sh
        SPEEDUP_WSL_PIP ?= DISPLAY= #
    endif
else
    PYTHON ?= python
    VENV_PYTHON ?= python.exe
endif
$/venv/bin/python3 := $/venv/$(VENV_PYTHON)

# Turn PYTHON into an explicit path
override PYTHON := $(shell which $(PYTHON))

# Figure out how to install packages into a PYTHON venv $/venv/bin/python3
ifndef PYTHON_NAME
    PYTHON_SITE_PACKAGES_DIR := $(shell $(PYTHON) -c "import sys; print('\n'.join(sys.path))" | grep site-packages)
    PYTHON_NAME := $(subst $~/.local/lib/%/site-packages,%,$(PYTHON_SITE_PACKAGES_DIR))

    # Workaround WSL python3 not having site-packages
    ifeq (,$(PYTHON_NAME))
    	PYTHON_NAME := python3
    endif

    # Workaround WSL python3 venv cashing pip wheels outside ~
    ifeq (/usr/bin/python3,$(PYTHON))
        PYTHON_DEP = /.cache/pip
        /.cache/pip:; sudo mkdir -p $@ && sudo chmod a+rwx $@
        PYTHON_FINALIZE = && $(SPEEDUP_WSL_PIP)$@ -m pip install --upgrade pip setuptools && $(SPEEDUP_WSL_PIP)$@ -m venv --upgrade $(patsubst %/bin/python3,%,$@)

    # Workaround Windows python not installing #!venv/bin/python3
    else ifeq (/mnt/c/tools/miniconda3/python.exe,$(PYTHON))
        PYTHON_FINALIZE = && mkdir -p $(dir $@) && ln -s ../Scripts/python.exe $@
    endif
endif
$/venv/pip/ := $/venv/lib/$(PYTHON_NAME)/site-packages

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

    # Install a package
    $?/%:; $! $*
endif


### Variables

#### Define the rest here only once

ifndef $/_NAME
$/_NAME := $(notdir $(realpath $/.))

#### Find subdirectories containing at least one .md file

$/_NON-SUBPROJECTS += $/build/
$/_SUBDIRS := $(foreach d,$(shell find $/. -mindepth 1 -maxdepth 1),$(notdir $d))
$/_SUBPROJECTS += $(sort $(dir $(foreach d,$($/_SUBDIRS),$(wildcard $/$d/*.md))))
$/_SUBPROJECTS := $(filter-out $($/_NON-SUBPROJECTS),$($/_SUBPROJECTS))
$/_ACTIVE_SUBPROJECTS := $(dir $(foreach d,$($/_SUBPROJECTS),$(wildcard $/$dMakefile)))

#### Make sub-projects before this project

$/all: | $($/_ACTIVE_SUBPROJECTS:%=%all)
$/tested: | $($/_ACTIVE_SUBPROJECTS:%=%tested)
$/report: | $($/_ACTIVE_SUBPROJECTS:%=%report)
$/gfm: | $($/_ACTIVE_SUBPROJECTS:%=%gfm)
$/pdf: | $($/_ACTIVE_SUBPROJECTS:%=%pdf)
$/html: | $($/_ACTIVE_SUBPROJECTS:%=%html)
$/slides: | $($/_ACTIVE_SUBPROJECTS:%=%slides)
$/old: | $($/_ACTIVE_SUBPROJECTS:%=%old)
$/new: $($/_ACTIVE_SUBPROJECTS:%=%new)
$/build/review.diff: $($/_ACTIVE_SUBPROJECTS:%=%build/review.diff)

#### Remove all built files in all projects
define META
    $/clean: $/clean_keep_venv | $($/_ACTIVE_SUBPROJECTS:%=%clean)
	    rm -rf $/venv/ $/.ruff_cache/
    $/clean_keep_venv: | $($/_ACTIVE_SUBPROJECTS:%=%clean)
	    rm -rf $/build/
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
.PRECIOUS: $/makemake.py $($/_SUBPROJECTS:%=%makemake.py)

# Notify the user if new rules were built and included, and make therefore restarted
ifeq (2,$(MAKE_RESTARTS))
    ifndef MAKER
        $(info # Hello $I, Welcome to makemake https://github.com/joakimbits/normalize)
    endif

    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $/build/
    $(info # $(PWD) $(filter-out $(INCLUDING)%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $($/venv/bin/python3))
    INCLUDED := $(MAKEFILE_LIST)
    INCLUDING := $/build/

    # Notify the user on abusage of make
    ifneq (0,$(MAKELEVEL))
        $(info # Warning: This is a recursive $(MAKE). Please use global variable names and include instead.)
        $(info # https://aegis.sourceforge.net/auug97.pdf)
        $(info # https://github.com/joakimbits/normalize/blob/main/example/Makefile)
    endif
endif

# Find all source files, but ignore links named Makefile *.h *.hpp *.py *.md 
$/_SOURCE :=
$/_MAKEFILE := $(shell find $/Makefile \! -type l 2>/dev/null)
$/_SOURCE += $($/_MAKEFILE)
$/*.s := $(wildcard $/*.s)
$/_SOURCE += $($/*.s)
$/*.c := $(wildcard $/*.c)
$(info DEBUG $/*.c = $($/*.c))
$/_SOURCE += $($/*.c)
$/*.h := $(shell find $/*.h \! -type l 2>/dev/null)
$/_SOURCE += $($/*.h)
$/*.cpp := $(wildcard $/*.cpp)
$/_SOURCE += $($/*.cpp)
$/*.hpp := $(shell find $/*.hpp \! -type l 2>/dev/null)
$/_SOURCE += $($/*.hpp)
$/*.py := $(shell find $/*.py \! -type l 2>/dev/null)
$(error DEBUG $/*.py = $($/*.py))
$/*.py := ($/*.py:./%=%)
$/_SOURCE += $($/*.py)
$/*.md := $(shell find $/*.md \! -type l 2>/dev/null)
$/_SOURCE += $($/*.md)

# Find our git status
$/_BRANCH := $(shell git branch --show-current)
$/_BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
$/_KNOWN := $(addprefix $/_,$(shell cd $/. ; git ls-files . ':!:*/*'))
$/_ADD := $(filter-out $($/_KNOWN),$($/_SOURCE))
$/_MODIFIED := $(shell cd $/. && $(PYTHON) makemake.py --git-status . M)
$/_REMOVE := $(filter-out $($/_SOURCE),$($/_KNOWN))

# Figure out where to checkout an old worktree
$/_HOME_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/_HOME := $($/_HOME_DIR:./%=%)
$/_HOME_NAME := $(notdir $(abspath $($/_HOME_DIR)))
$/_GIT_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/_HERE_DIR := $(shell $(PYTHON) $/makemake.py --relpath $($/_GIT_DIR) $/.)/
$/_HERE := $($/_HERE_DIR:%./=%)
$/_OLD_WORKTREE := $($/_HOME)build/$($/_BASELINE)/$($/_HOME_NAME)/
$/_OLD := $($/_OLD_WORKTREE)$($/_HERE)

## Colorize edited files by their git status
NORMAL ?= `tput sgr0`
RED ?= `tput setaf 1`
GREEN ?= `tput setaf 2`
YELLOW ?= `tput setaf 3`
BLUE ?= `tput setaf 4`
REVERSED ?= `tput rev`
$/_BRANCH_STATUS := $(if $($/_ADD),$(RED)$($/_ADD)$(NORMAL))
$/_BRANCH_STATUS += $(if $($/_MODIFIED),$(BLUE)$($/_MODIFIED)$(NORMAL))
$/_BRANCH_STATUS += $(if $($/_REMOVE),$(REVERSED)$($/_REMOVE)$(NORMAL))
$/_COMMIT_INFO := $(shell git log -1 --oneline $/.)
$/_BRANCH_STATUS += $($/_COMMIT_INFO)

ifeq ($(filter v%,$($/_BASELINE)),)
    $/_BASELINE_INFO := $(shell git show --oneline -s $($/_BASELINE))
else
    $/_BASELINE_INFO := $(strip $(shell git tag --list $($/_BASELINE) -n1))
endif

$/_CHANGES := $($/_BASELINE_INFO) --> $($/_BRANCH_STATUS)
$/_CHANGES_AUDIT := $($/_BASELINE_INFO) -->
$/_CHANGES_AUDIT += $($/_ADD)
$/_CHANGES_AUDIT += $($/_MODIFIED)
$/_CHANGES_AUDIT += $($/_COMMIT_INFO)

# Collect code
$/_LINKABLE := $($/*.s)
$/_COMPILABLE := $($/*.c)
$/_COMPILABLE += $($/*.cpp)
$/_LINKABLE += $($/_COMPILABLE)
$/_CODE := $($/_SRCS)
$/_CODE += $($/*.py)

## Prepare for clang compilation
$/_LDFLAGS := $(LDFLAGS)
$/_LDFLAGS += -mabi=aapcs-linux

# A linked executable has the same name as the project
ifneq (,$(strip $($/_LINKABLE)))
    $/_EXE := $/$($/_NAME)
    $/_EXE_TESTED := $/build/$($/_NAME).tested
endif

# If we got assembly source, assume it has _start code
ifneq ($(strip $($/*.s)),)
    $/_LDFLAGS += -nostartfiles -no-pie
endif

$/_CXXFLAGS := $($/_LDFLAGS)
$/_CXXFLAGS += -S $(addprefix -I,$($/_INC_DIRS)) -MMD -MP
$/_CFLAGS := $($/_CXXFLAGS)
$/_CXXFLAGS += $(CXXFLAGS)
$/_CFLAGS += $(CFLAGS)
$/_COBJS := $($/_COMPILABLE:$/%=$/build/%.s)
$/_DEPS += $($/_COBJS:.s=.d)
$/_OBJS := $($/*.s)
$/_OBJS += $($/_COBJS)
$/_EXES := $($/_EXE)
$/_EXES += $($/*.py)

# Collect bringup and tested targets
$/_BRINGUP := $($/*.py:$/%=$/build/%.bringup)
$/_TESTED += $($/*.py:$/%=$/build/%.tested)
$/_PRETESTED := $($/_TESTED)
$/_TESTED += $($/*.md:$/%=$/build/%.sh-test.tested)

# Prepare for bringup
$/build/*.py.mk := $($/*.py:$/%=$/build/%.mk)
$/_DEPS += $($/build/*.py.mk)

# Prepare for reporting
$/_LOGIC := $($/_MAKEFILE)
$/_LOGIC += $($/_CODE)
$/_RESULT := $($/build/*.py.mk)
$/_RESULT += $($/_BRINGUP)
$/_RESULT += $($/_TESTED)
$/_REPORT := $/build/report-details.md
$/_REPORT += $($/_LOGIC:$/%=$/build/%.md)
$/_REPORT += $($/_RESULT:%=%.md)

## Targets

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Do not use any built-in rules
.SUFFIXES:

# Convenience targets
.PHONY: $/bringup $/tested $/clean
$/bringup: $($/_EXE) $($/_BRINGUP)
$/tested: $($/_TESTED)

# Use the clang compiler
$?/clang++: $?/clang
CXX := /usr/bin/clang++
CC := /usr/bin/clang

# Make executable
ifneq (,$($/_OBJS))
    $/build/$($/_NAME).tested: $/$($/_NAME)
	    true | ./$< > $@ || (cat $@ && false)

    # Use project specific compile flags
    define META
        # Compile C++
        $/build/%.cpp.s: $/%.cpp | $(CXX)
	        $(CXX) $($/_CXXFLAGS) -c $$< -o $$@

        # Compile C
        $/build/%.c.s: $/%.c | $(CC)
	        $(CC) $($/_CFLAGS) -c $$< -o $$@

        # Link executable
        $/$($/_NAME): $($/_OBJS) | $(CC)
	        $(CC) $($/_LDFLAGS) $$^ -o $$@
    endef
    $(eval $(META))
endif

# Check Python 3.9 syntax
$/syntax: $/build/syntax
$/build/%.py.syntax: $($/venv/bin/python3) $/%.py | $($/venv/pip/)ruff
	$< -m ruff --select=E9,F63,F7,F82 --target-version=py39 $(lastword,$^) > $@ || (cat $@ && false)

# Install pip package in the local python:
$($/venv/pip/)%: $($/venv/bin/python3)
	 $< -m pip install $*

# Setup a local shebang python
$/venv/bin/python3: | $(PYTHON) $(PYTHON_DEP) $(.-ON-PATH) $(SPEEDUP_WSL_DNS)
	$(SPEEDUP_WSL_PIP)$(PYTHON) -m venv $(@:%/bin/python3=%) $(PYTHON_FINALIZE)
	$(SPEEDUP_WSL_PIP)$@ -m pip install requests  # Needed by -m makemake --prompt

# Install conda python
ifndef CONDA
    CONDA := ~/miniconda3/bin/cond
    ~/miniconda3/bin/conda:
	    curl -sL https://repo.anaconda.com/miniconda/Miniconda3-latest-$(OS)-$(CPU).sh > miniconda.sh
	    bash miniconda.sh -bfup $~/miniconda3
	    rm miniconda.sh
endif

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

# Check Python 3.9 style
$/build/%.py.style: $/%.py $/build/%.py.syntax $($/venv/bin/python3)
	$(word 3,$^) -m ruff --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Build a recipy for $/build/%.py.bringup
$/build/%.py.mk: $/. $/%.py
	rm -f $@ && ( cd $< && $(PYTHON) $*.py --generic --dep $(@:$(dir $<)%=%) ) ; [ -e $@ ] || echo "\$$build/$*.py.bringup:; touch \$$@" > $@

# Check Python and command line usage examples in .py files
$/build/%.py.tested: $/. $/%.py $/build/%.py.mk $/build/%.py.style $/build/%.py.bringup $($/_EXE_TESTED) | $($/venv/bin/python3)
	( cd $< && $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$/build/%.sh-test.tested: $/. $($/_PRETESTED) $/build/%.sh-test | $/makemake.py
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $< && $(PYTHON) makemake.py --timeout 60 --sh-test $(patsubst $(dir $<)%,%,$(lastword $^)) ) > $$tmp && mv $$tmp $@
$($/build/%.md.sh-test: $/%.md | $?/pandoc $?/jq)
$/build/%.md.sh-test: $/%.md | $?/pandoc $?/jq
	pandoc -i $< -t json --preserve-tabs | jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && truncate -s -1 $@

# Document all test results.
$/report: $/build/report.txt
	@cat $<
$/build/report.txt: $($/_TESTED)
	( $(foreach t,$^,echo "___ $(t): ____" && cat $(t) ; ) ) > $@

# Make a standalone html, pdf, gfm or dzslides document.
define META
    $/%.gfm: $/build/%.md
	pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	       -M title="$($/_NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`"
    $/%.html $/%.pdf $/%.dzslides: $/build/%.md | \
      $?/pandoc $?/xelatex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	    pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	           -M title="$$($/_NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`" \
	           -V min-width=80%\!important -V geometry:margin=1in \
	           --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"
endef
$(eval $(META))

# Make a markdown document.
$/_h := \n---\n\n\#
$/_~~~. = \\footnotesize\n~~~ {$1}
$/_~~~sh := $(call $/_~~~.,.sh)
$/_~~~ := ~~~\n\\normalsize\n
define META
    $/build/Makefile.md: project.mk
	    ( echo "$($/_h)## [$$*]($$*)" && \
	      echo "$(call $/_~~~.,.mk)" && \
	      cat $$< && echo "$($/_~~~)" ) > $$@
    $/build/%.md: $/%
	    ( echo "$($/_h)## [$$*]($$*)" && \
	      echo "$(call $/_~~~.,$$(suffix $$<))" && \
	      cat $$< && echo "$($/_~~~)" ) > $$@
    $/build/%.md: $/build/%
	    ( echo "$($/_h)## [$$*](build/$$*)" && \
	      echo "$(call $/_~~~.,$$(suffix $$<))" && \
	      cat $$< && echo "$($/_~~~)" ) > $$@
    $/build/%.bringup.md: $/build/%.bringup
	    ( echo "$($/_h)## [$$*](build/$$*)" && \
	      echo "$($/_~~~sh)" && \
	      cat $$< && echo "$($/_~~~)" ) > $$@
    $/build/%.tested.md: $/build/%.tested
	    ( echo "$($/_h)## [$$*](build/$$*)" && \
	      echo "$($/_~~~sh)" && \
	      cat $$< && echo "$($/_~~~)" ) > $$@
endef
$(eval $(META))

# Report the project.
define META
    $/%: $/report.%
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $($/_BRANCH_STATUS)"
    $/slides: $/slides.html
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $($/_BRANCH_STATUS)"
endef
$(eval $(META))
$/slides.html: $/report.dzslides
	mv $< $@
$/report.html $/report.pdf $/report.gfm $/report.dzslides: $($/*.md) $($/_REPORT)
$/_file = $(foreach _,$1,[\`$_\`]($_))
$/_exe = $(foreach _,$1,[\`$_\`]($_))
$/_h_fixup := sed -E '/^$$|[.]{3}/d'
#define META
    $/build/report.md: $/build/report.txt
	    echo "A build-here include-from-anywhere project based on [makemake](https://github.com/joakimbits/normalize)." > $$@
	    echo "\n- \`make report pdf html slides review audit\`" >> $$@
ifneq ($(strip $($/_EXE)),)
	    echo "- \`./$($/_NAME)\`: $(call $/_file,$($/_SRCS:$/%=%))" >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- $(call $/_exe,$($/*.py:$/%=%))" >> $$@
endif
	    echo "$($/_h)## Installation" >> $$@
	    echo "$($/_~~~sh)" >> $$@
	    echo "\$$ make" >> $$@
	    echo "$($/_~~~)" >> $$@
ifneq (,$(strip $($/_EXE)))
	    echo "- Installs \`./$($/_NAME)\`." >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- Installs \`venv\`." >> $$@
	    echo "- Installs \`$(call $/_exe,$($/*.py:$/%=%))\`." >> $$@
endif
ifneq (,$($/_EXES))
	    echo "$($/_h)## Usage" >> $$@
	    echo "$($/_~~~sh)" >> $$@
	    for x in $($/_EXES:$/%=%)) ; do \
	      echo "\$$$$ true | $$$$x -h | $($/_h_fixup)" >> $$@ && \
	      ( cd $/. && true | $$$$x -h ) > $$@.tmp && \
	      $($/_h_fixup) $$@.tmp >> $$@ && rm $$@.tmp ; \
	    done
	    echo >> $$@
	    echo "$($/_~~~)" >> $$@
	    echo "$($/_h)## Test" >> $$@
	    echo "$($/_~~~sh)" >> $$@
	    echo "\$$$$ make tested" >> $$@
	    echo "$($/_~~~)" >> $$@
endif
ifneq (,$(strip $($/_EXE)))
	    echo "- Tests \`./$($/_NAME)\`." >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- Verifies style and doctests in $(call $/_file,$($/*.py:$/%=%)))." >> $$@
endif
ifneq (,$(strip $($/*.md)))
	     echo "- Verifies doctests in $(call $/_file,$($/*.md:$/%=%)))." >> $$@
endif
ifneq (,$(strip $($/_CODE)))
	    echo "$($/_h)## Result" >> $$@
	    echo "$($/_~~~sh)" >> $$@
	    echo "\$$$$ make report" >> $$@
	    ( cd $/. && $(MAKE) report --no-print-directory ) >> $$@
	    echo "$($/_~~~)" >> $$@
	    echo "\n---\n" >> $$@
endif
#endef
#$(eval $(META))
$/build/report-details.md:
	echo "$($/_h)# Source code, installation and test result" >> $@

# Build an old worktree that is shared by all projects in this git
ifndef _OLD_WORKTREE
    _OLD_WORKTREE := $($/_OLD_WORKTREE)
    $(_OLD_WORKTREE):
	    git worktree add -d $(_OLD_WORKTREE) $($/_TAG)
endif

# Document last release.
$/old: $($/_OLD)report.gfm
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/_BASELINE_INFO)"
$($/_OLD)report.gfm: $(_OLD_WORKTREE)
	( cd $($/_OLD) && $(MAKE) report.gfm --no-print-directory )

# Use GPT for a release review.
$/%: $/build/%.diff
	cat $<
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/_CHANGES)"
define META
    $/build/audit.diff: $/build/prompt.diff | $($/venv/bin/python3)
	    cat $$< > $$@
	    $($/venv/bin/python3) -m makemake --prompt $$< $(GPT_MODEL) $(GPT_TEMPERATURE) $(GPT_BEARER_rot13) >> $$@
endef
$(eval $(META))
$/build/prompt.diff: $/build/review.diff
	$(PYTHON) $/makemake.py -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $/review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$/build/review.diff: $/build/files.diff $/build/comments.diff $/build/report.diff
	cat $^ > $@
$/build/files.diff:
	echo "# $($/_CHANGES_AUDIT)" > $@
define META
    $/build/comments.diff:
	    echo "git --no-pager log --no-merges $($/_BASELINE)..HEAD $/." > $$@
	    git --no-pager log --no-merges $($/_BASELINE)..HEAD $/. >> $$@
endef
$(eval $(META))
$/build/report.diff: $($/_OLD)report.gfm $/report.gfm $/makemake.py
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
$/_DEPS += $($/_SUBPROJECTS:%=%Makefile)
$/_DEPS := $(filter-out $($/_NON-DEPS),$($/_DEPS))
-include $($/_DEPS)

endif # first time
