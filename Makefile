### Abstract

# Defines generic make targets `bringup tested report review audit clean clean/keep_venv` for arbitrarily knitted projects.

# Can be included in any other project.

# Will always make project files in the same location.

# Warns if building recursively rather than being included, but still makes the same.

# Developed on x86 WSL1 and Arm64 MacOSX.

# Release-tested on GitHub.

# Work in progress: Support also review/audit on bare MacOSX and bare Windows, where a diff command is missing.

### Usage

# Copy the following four lines into the head of your own Makefile, to make it compliant with this.

    # Prefixing project variable names with $/_ and project files with $/ to make this Makefile usable from anywhere.
    Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))
    $/bringup:

# Define this project only once
ifndef $/_NAME
$/make: $/build/project.mk

# Define generic examples only once
ifndef _NAME
_NAME := $(notdir $(realpath $/.))

### Avoid using make as a command recipy tool - it is not!

# If $/ *is* used within a recipy, that whole recipy needs to be expanded before the rule is defined, like this:

    define META
        $$/meta-recipy:
	        # $$@: $$^ - Every $$ except a wanted expansion of $$/ = $/ in the recipy needs to be doubled now!
	        echo "Like this: $$$$$$$$PATH = $$$$PATH"
	        # And the recipy itself needs to be be defined by`$$(eval ...)`-ing it first.
    endef
    $(eval $(META))

    $/normal-target: $/this-is-much-better
	    # $@: $^ - This rule expansion from $$/ is available in recipy variables $$@: $$^.
	    touch $@
	    # This recipy will not execute again unless an update is actually needed, because $$/normal-target *was touched*.
    $/this-is-much-better: ; touch $@

    .PHONY: $/normal-target # This is how to force that recipy to re-execute every `make` where $/normal-target is needed.
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

# `bringup`: All code in the project is executable as bare shell commands, including .py files.
# `build/*.py.bringup`: *.py is executable by the venv/bin/python3 next to it.
# `build/*.py.shebang`: *.py has the local python shebang #!venv/bin/python3
# `build/directory-name.bringup`: directory-name is an executable that contains all compilable sources.
# `build/*.tested`: * is self-tested without failure, and the test output is here.
# `build/*.md`: * is documented here. Make *.gfm *.pdf *.html to translate it to your desired pandoc format.

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
# Python code is assumed to import build and will then get a Shebang that works *here* only.

# In a Makefile:

    $/greeter.txt: $/example/bin/python3 $/example/greeter.py $/example/build/greeter.py.bringup; $(wordlist 1,2,$^) > $@
    $/tested-greeter.txt: $/example/bin/python3 $/example/greeter.py $/example/build/greeter.py.tested; $(wordlist 1,2,$^) > $@

# In a shell:
$/python_executable_shell_example:

	make && ( cd example && greeter.py ) > greeter-from-shell.txt
	make tested && ( cd example && greeter.py ) > tested-greeter-from-shell.txt

# In Python:

#   * Copy its `Dependencies:` into your own .py header.
#   * `touch __init__.py` on the complete path to it. Now you can import and use it.

	touch example/__init__.py
	venv/bin/python3 -c "import example; open('greeter-from-py.txt).write(example.greeter.hello())"


endif # generic examples
$/_NAME := $(notdir $(realpath $/.))


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

    # Prefixing project variable names with $/_ and project files with $/ to make this Makefile usable from anywhere
    Makefile := $(lastword $(MAKEFILE_LIST))
    / := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))
    $/bringup:

    # Bringup executables from any source files here, and define 'report html pdf slides audit' targets here.
    $/build/project.mk:
	    mkdir -p $(dir $@) && curl https://raw.githubusercontent.com/joakimbits/normalize/main/Makefile -o $@

    $/_NON-SUBPROJECTS += $/this
    # $/_DEPS += $/this/Makefile
    #-include $/build/project.mk

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
$/venv/pip/ := $/venv/lib/$(PYTHON_NAME)/site-packages/

# A package manager for the PYTHON OS
ifndef !
    UNAME ?= $(shell which uname)
    ifeq (,$(UNAME))
        UNAME := $(PYTHON) -m build
    endif

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
        /usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf:
	        # Need a more screen-readable normal font: carlito
	        sudo apt-get install fonts-crosextra-carlito
        /usr/share/fonts/truetype/cousine/Cousine-Regular.ttf:
	        # Need a more screen-readable fixed-size font: cousine
	        ( sudo mkdir -p $(dir $@) && cd $(dir $@) && \
	          fonts=https://raw.githubusercontent.com/google/fonts/main/apache && \
	          sudo wget $$fonts/cousine/DESCRIPTION.en_us.html && \
	          sudo wget $$fonts/cousine/Cousine-Bold.ttf && \
	          sudo wget $$fonts/cousine/Cousine-BoldItalic.ttf && \
	          sudo wget $$fonts/cousine/Cousine-Italic.ttf && \
	          sudo wget $$fonts/cousine/Cousine-Regular.ttf )
    endif

    # Install a normal package
    $?/%:; $! $*

    # Custom packages
    $?/xetex:; $! texlive-xetex
endif


### Variables

#### Find subdirectories containing at least one .md file

$/_NON-SUBPROJECTS += $/build/
$/_SUBDIRS := $(foreach d,$(shell find $/. -mindepth 1 -maxdepth 1),$(notdir $d))
$/_SUBPROJECTS += $(sort $(dir $(foreach d,$($/_SUBDIRS),$(wildcard $/$d/*.md))))
$/_SUBPROJECTS := $(filter-out $($/_NON-SUBPROJECTS),$($/_SUBPROJECTS))
$/_ACTIVE_SUBPROJECTS := $(dir $(foreach d,$($/_SUBPROJECTS),$(wildcard $/$dMakefile)))

# Define symbolic targets we might want to use to represent (all) its dependencies
# Do not use such a phony as a dependency unless you also need the target rebuilt every time.
define META
    .PHONY: $/bringup $/syntax $/style $/tested $/old $/new
    .PHONY: $/make $venv $/slides $/clean $/clean/keep_venv $/list
    $/make: | $($/_ACTIVE_SUBPROJECTS:%=%make)
    $/bringup: | $($/_ACTIVE_SUBPROJECTS:%=%bringup)
    $/tested: | $($/_ACTIVE_SUBPROJECTS:%=%tested)
    $/html: | $($/_ACTIVE_SUBPROJECTS:%=%html)
    $/pdf: | $($/_ACTIVE_SUBPROJECTS:%=%pdf)
    $/slides: | $($/_ACTIVE_SUBPROJECTS:%=%slides)
    $/old: | $($/_ACTIVE_SUBPROJECTS:%=%old)
    $/new: | $($/_ACTIVE_SUBPROJECTS:%=%new)
    $/clean: $/clean/keep_venv | $($/_ACTIVE_SUBPROJECTS:%=%clean)
	    rm -rf $/venv/ $/.ruff_cache/
    $/clean/keep_venv: | $($/_ACTIVE_SUBPROJECTS:%=%clean/keep_venv)
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

# Find our git status
$/_BRANCH := $(shell git branch --show-current)
$/_KNOWN := $(addprefix $/,$(shell cd $/. ; git ls-files . ':!:*/*'))
$/_ADD := $(filter-out $($/_KNOWN),$($/_SOURCE))
$/_MODIFIED := $(shell cd $/. && $(PYTHON) -m build --git-status . M)
$/_REMOVE := $(filter-out $($/_SOURCE),$($/_KNOWN))
$/_HOME_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/_HOME := $($/_HOME_DIR:./%=%)
$/_HOME_NAME := $(shell basename `git rev-parse --show-toplevel`)

# Setup this Makefile in each subproject
$/%/Makefile: | $/Makefile $/%/build.py
	ln -s ../Makefile $@
$/%/build.py: | $/build.py
	ln -s ../build.py $@
$/build.py:
	mkdir -p $(dir $@) && curl https://raw.githubusercontent.com/joakimbits/normalize/main/build.py -o $@

.PRECIOUS: $/build.py $($/_SUBPROJECTS:%=%build.py)

# Find all source files, but ignore links named Makefile *.h *.hpp *.py *.md
$/_SOURCE :=
$/_MAKEFILE := $(shell find $/Makefile \! -type l 2>/dev/null)
$/_SOURCE += $($/_MAKEFILE)
$/*.s := $(wildcard $/*.s)
$/_SOURCE += $($/*.s)
$/*.c := $(wildcard $/*.c)
$/_SOURCE += $($/*.c)
$/*.h := $(shell find $/*.h \! -type l 2>/dev/null)
$/_SOURCE += $($/*.h)
$/*.cpp := $(wildcard $/*.cpp)
$/_SOURCE += $($/*.cpp)
$/*.hpp := $(shell find $/*.hpp \! -type l 2>/dev/null)
$/_SOURCE += $($/*.hpp)
$/*.py := $(shell find $/*.py \! -type l 2>/dev/null)
ifneq (normalize ./,$($/_HOME_NAME) $($/_HOME_DIR))
    $/*.py := $(filter-out $/build.py,$($/*.py))
	$/_DEPS += $/build/build.py.mk
endif
$/_SOURCE += $($/*.py)
$/*.md := $(shell find $/*.md \! -type l 2>/dev/null)
$/_SOURCE += $($/*.md)

# Checkout a common old release of this repo as a subproject in `$($._BASELINE)`
# Prefix `$/_HERE` is from this git project root directory to  `./`.
# Directory `$($/_OLD)` is the old release of `./`.
$/_HERE_DIR := $(dir $(shell $(PYTHON) $/build.py --relpath $($/_HOME_DIR) $/.))
$/_HERE := $($/_HERE_DIR:./%=%)
$/_BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
$/_OLD := $($/_HOME)build/$($/_BASELINE)/$($/_HOME_NAME)/$/
ifndef $($/_HOME_DIR)
    $($/_HOME_DIR) := $($/_HOME_DIR))
    define META
        $$($$/_OLD)Makefile:
	        git worktree add -d $$(dir $$@) $$($/_BASELINE)
    endef
    $(eval $(META))
endif

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
$/_CODE := $($/_LINKABLE)
$/_CODE += $($/*.py)

## Prepare for compilation
$/_LDFLAGS += $(LDFLAGS)

# A linked executable has the same name as the project
ifneq (,$($/_LINKABLE))
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
$/build/*.bringup := $($/_EXES:$/%=$/build/%.bringup)
$/build/*.bringup += $($/*.py:$/%=$/build/%.shebang)
$/build/*.tested += $($/_EXES:$/%=$/build/%.tested)
ifndef PRETESTED
    PRETESTED :=
    TESTED :=
endif
PRETESTED += $($/build/*.tested)
$/build/*.tested += $($/*.md:$/%=$/build/%.sh-test.tested)
TESTED += $($/build/*.tested)

# Prepare for bringup
$/build/*.py.mk := $($/*.py:$/%=$/build/%.mk)
$/_DEPS += $($/build/*.py.mk)

# Prepare for reporting
$/_LOGIC := $($/_MAKEFILE)
$/_LOGIC += $($/_CODE)
$/_RESULT := $($/build/*.py.mk)
$/_RESULT += $($/build/*.bringup)
$/_RESULT += $($/build/*.tested)
$/_REPORT := $/build/report-details.md
$/_REPORT += $($/_LOGIC:$/%=$/build/%.md)
$/_REPORT += $($/_RESULT:%=%.md)

# Notify the user if new rules were built and included, and make therefore restarted
ifeq (2,$(MAKE_RESTARTS))
    ifndef MAKER
        $(info # Hello $I, Welcome to generic make https://github.com/joakimbits/normalize)
    endif

    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $/build/
    $(info # $(PWD) $(filter-out $(INCLUDING)%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $($/venv/bin/python3))
    INCLUDED := $(MAKEFILE_LIST)
    INCLUDING := $/build/
    ifneq (,$($/_SUBPROJECTS))
        $(info $/_SUBPROJECTS = $($/_SUBPROJECTS))
    endif

    # Notify the user on abusage of make
    ifneq (0,$(MAKELEVEL))
        $(info # Warning: This is a recursive $(MAKE). Please use global variable names and include instead.)
        $(info # https://aegis.sourceforge.net/auug97.pdf)
    endif
endif


## Targets

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Do not use any built-in rules
.SUFFIXES:

# Convenience targets
define META
    $/venv: $/venv/bin/python3
    $/bringup: $($/_EXE) $($/build/*.bringup)
    $/tested: $($/build/*.tested)
    $/syntax: $($/*.py:$/%=$/build/%.syntax)
    $/style: $($/*.py:$/%=$/build/%.style)
    $/old: $($/_OLD)report.gfm
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $$($/_BASELINE_INFO)"
    $/new: $/report.gfm
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $$($/_BRANCH_STATUS)"
    $/%: $/report.%
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $$($/_BRANCH_STATUS)"
    $/slides: $/slides.html
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $$($/_BRANCH_STATUS)"
    $/%: $/build/%.diff
	    @echo "# file://$$(subst /mnt/c/,/C:/,$$(realpath $$<)) $$($/_CHANGES)"
endef
$(eval $(META))

$/slides.html: $/report.dzslides
	cp $< $@

# Use the clang compiler
$?/clang++: $?/clang
CXX := /usr/bin/clang++
CC := /usr/bin/clang

# Make a linked executable
ifneq (,$($/_OBJS))
    $/build/$($/_NAME).tested: $/$($/_NAME)
	    true | ./$< > $@ || (cat $@ && false)

    # Use project specific compile flags
    define META
        # Compile C++
        $$/build/%.cpp.s: $$/%.cpp | $$(CXX)
	        $$(CXX) $$($/_CXXFLAGS) -c $$< -o $$@

        # Compile C
        $$/build/%.c.s: $$/%.c | $$(CXX)
	        $$(CXX) $$($/_CFLAGS) -c $$< -o $$@

        # Link executable
        $$/$$($$/_NAME): $$($$/_OBJS) | $$(CC)
	        $$(CC) $$($/_LDFLAGS) $$^ -o $$@
    endef
    $(eval $(META))
endif

# Build a recipy for $/build/%.py.bringup
$/build/%.bringup: $/%
	mkdir -p $(dir $@) && touch $@

# Make a Python executable
$/build/%.py.shebang: $($/venv/bin/python3) $/%.py
	$^ --shebang > $@

# Build a recipy for $/build/%.py.bringup
$/build/%.py.mk: $/%.py | $/build.py
	rm -f $@ && ( cd $(dir $<). && $(PYTHON) $*.py --generic --dep build/$*.py.mk ) ; [ -e $@ ] || echo "\$$/build/$*.py.bringup:; touch \$$@" > $@

# Check Python 3.9 syntax
$/build/%.py.syntax: $($/venv/bin/python3) $/%.py | $($/venv/pip/)ruff
	$< -m ruff check --select=E9,F63,F7,F82 --target-version=py39 $(lastword,$^) > $@ || (cat $@ && false)

# Install pip package in the local python:
$($/venv/pip/)%: $($/venv/bin/python3)
	 $< -m pip install $*

# Setup a local shebang python
$/venv/bin/python3: | $(PYTHON) $(PYTHON_DEP) $(.-ON-PATH) $(SPEEDUP_WSL_DNS)
	$(SPEEDUP_WSL_PIP)$(PYTHON) -m venv $(@:%/bin/python3=%) $(PYTHON_FINALIZE)
	$(SPEEDUP_WSL_PIP)$@ -m pip install requests  # Needed by -m build --prompt

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
	$(word 3,$^) -m ruff check --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Check Python and command line usage examples in .py files
$/build/%.py.tested: $/. $/%.py $/build/%.py.mk $/build/%.py.style $/build/%.py.bringup $/build/%.py.shebang $($/_EXE_TESTED) | $($/venv/bin/python3)
	( cd $< && $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$/build/%.sh-test.tested: $/. $(PRETESTED) $/build/%.sh-test | $/build.py
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $< && $(PYTHON) -m build --timeout 60 --sh-test $(patsubst $(dir $<)%,%,$(lastword $^)) ) > $$tmp && mv $$tmp $@
$/build/%.md.sh-test: $/%.md | $?/pandoc $?/jq
	mkdir -p $(dir $@) && pandoc -i $< -t json --preserve-tabs | jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && truncate -s -1 $@

# Document all test results.
$/report: $/build/report.txt
	@cat $<
$/build/report.txt: $(TESTED)
	( $(foreach t,$^,echo "___ $(t): ____" && cat $(t) ; ) ) > $@

# Make a markdown document.
ifndef __
    _file = $(foreach _,$1,[\`$_\`]($_))
    _exe = $(foreach _,$1,[\`$_\`]($_))
    _help_fixup := sed 's/^/\t/'
    _heading := \n---\n\n\#
    _link = [$1]($1)
    _. = \\\\footnotesize\n~~~ {$1}
    _sh := $(call _.,.sh)
    __ := ~~~\n\\\\normalsize\n
endif

$/build/Makefile.md: $/Makefile
	( echo "$(_heading)## $(call _link,Makefile)" && echo "$(call _.,.mk)" && cat $< && echo "$(__)" ) > $@
$/build/%.md: $/%
	( echo "$(_heading)## $(call _link,$*)" && echo "$(call _.,$(suffix $<))" && cat $< && echo "$(__)" ) > $@
$/build/%.md: $/build/%
	( echo "$(_heading)## $(call _link,build/$*)" && echo "$(call _.,$(suffix $<))" && cat $< && echo "$(__)" ) > $@
$/build/%.bringup.md: $/build/%.bringup
	( echo "$(_heading)## $(call _link,build/$*.bringup)" && echo "$(_sh)" && cat $< && echo "$(__)" ) > $@
$/build/%.tested.md: $/build/%.tested
	( echo "$(_heading)## $(call _link,build/$*.tested)" && echo "$(_sh)" && cat $< && echo "$(__)" ) > $@

# Make a standalone gfm, html, pdf, or dzslides document.
define META
    $$/build/report.md: $($/build/*.tested)
	    echo "A build-here include-from-anywhere project based on [normalize](https://github.com/joakimbits/normalize)." > $$@
	    echo "\n- \`make report pdf html slides review audit\`" >> $$@
ifneq ($(strip $($/_EXE)),)
	    echo "- \`./$$($/_NAME)\`: $$(call _file,$$($/_LINKABLE:$/%=%))" >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- $$(call _exe,$$($/*.py:$/%=%))" >> $$@
endif
	    echo "$$(_heading)## Installation" >> $$@
	    echo "$$(_sh)" >> $$@
	    echo "$$$$ make" >> $$@
	    echo "$$(__)" >> $$@
ifneq (,$(strip $($/_EXE)))
	    echo "- Installs \`./$$($/_NAME)\`." >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- Installs $$(call _exe,venv/bin/python3)." >> $$@
	    echo "- Installs $$(call _exe,$$($/*.py:$/%=%))." >> $$@
endif
ifneq (,$($/_EXES))
	    echo "$$(_heading)## Usage" >> $$@
	    echo "$$(_sh)" >> $$@
	    for x in $$($/_EXES:$/%=%) ; do \
	      echo "\$$$$ true | $$$$x -h | $$(_help_fixup)" >> $$@ && \
	      ( cd $/. && true | $$$$x -h ) > $$@.tmp && \
	      $$(_help_fixup) $$@.tmp >> $$@ && rm $$@.tmp ; \
	    done
	    echo >> $$@
	    echo "$$(__)" >> $$@
	    echo "$$(_heading)## Test" >> $$@
	    echo "$$(_sh)" >> $$@
	    echo "\$$$$ make tested" >> $$@
	    echo "$$(__)" >> $$@
endif
ifneq (,$(strip $($/_EXE)))
	    echo "- Tests \`./$$($/_NAME)\`." >> $$@
endif
ifneq (,$(strip $($/*.py)))
	    echo "- Verifies style and doctests in $$(call _file,$$($/*.py:$/%=%))." >> $$@
endif
ifneq (,$(strip $($/*.md)))
	     echo "- Verifies doctests in $$(call _file,$$($/*.md:$/%=%))." >> $$@
endif
ifneq (,$(strip $($/_CODE)))
	    echo "$$(_heading)## Result" >> $$@
	    echo "$$(_sh)" >> $$@
	    echo "\$$$$ make report" >> $$@
	    ( cd $/. && $$(MAKE) report --no-print-directory ) >> $$@
	    echo "$$(__)" >> $$@
	    echo "\n---\n" >> $$@
endif

    $$/%.gfm: $/build/%.md
	    pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	           -M title="$$($/_NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`"
    $$/%.html $$/%.pdf $$/%.dzslides: $$/build/%.md | $$?/pandoc $$?/xetex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	    pandoc --standalone -t $$(patsubst .%,%,$$(suffix $$@)) -o $$@ $$^ \
	           -M title="$$($/_NAME) $$*" -M author="`git log -1 --pretty=format:'%an'`" \
	           -V min-width=80%\!important -V geometry:margin=1in \
	           --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"
endef
$(eval $(META))
$/report.gfm $/report.html $/report.pdf $/report.dzslides: $($/*.md) $($/_REPORT)

$/build/report-details.md:
	echo "$(_heading)# Source code, installation and test result" >> $@

$($/_OLD)report.gfm: $($/_OLD)Makefile
	mkdir -p $(dir $@) && ( cd $(dir $@) && $(MAKE) report.gfm --no-print-directory ) || touch $@

# Use GPT for a release review.
$/build/audit.diff: $/build.py $/build/prompt.diff $/build/build.py.bringup
	( cd $(dir $<) && venv/bin/python3 -m build --prompt build/prompt.diff $(GPT_MODEL) $(GPT_TEMPERATURE) $(GPT_BEARER_rot13) ) > $@ && cat $(word 2,$^) $@ || ( cat $@ && false )
$/build/prompt.diff: $/build/review.diff
	$(PYTHON) -m build -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $/review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$/build/review.diff: $/build/files.diff $/build/comments.diff $/build/report.diff
	cat $^ > $@
$/build/files.diff: $($/build/*.tested)
	echo "# $($/_CHANGES_AUDIT)" > $@

define META
    $$/build/comments.diff: $($/build/*.tested)
	    echo "git --no-pager log --no-merges $$($/_BASELINE)..HEAD $/." > $$@
	    git --no-pager log --no-merges $$($/_BASELINE)..HEAD $/. >> $$@
endef
$(eval $(META))

$/build/report.diff: $($/_OLD)report.gfm $/report.gfm $/build.py
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

# List all targets that needs rebuilding and stop
$/list: $($/Makefile)
	make -f $< -dn MAKE=: $(filter-out $@,$(MAKECMDGOALS)) | sed -rn "s/^ *Must remake target '(.*)'\.$$/\1/p" && false

## Finally attempt to include all bringup files and sub-projects
# Note: Subprojects modify $/, so this has to be the last command using it as a prefix here.
$/_DEPS += $($/_SUBPROJECTS:%=%Makefile)
$/_DEPS := $(filter-out $($/_NON-DEPS),$($/_DEPS))
-include $($/_DEPS)

endif # first time
