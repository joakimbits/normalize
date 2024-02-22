# {_}$ {" ".join(sys.argv)}
# {" ".join(sys.argv)} = Command used to generate this file
# {build_dir} = sub-directory-for-intermediate-files
# {makemake_py} = path-to-makemake.py

# Configure a GPT model to use for `audit`
#  - A large-context openai model suitable for code review
#  - A rot13 encoded openai Bearer key for its GPT session.
#  - A temperature for its openai continuation.
GPT_MODEL ?= gpt-3.5-turbo-16k
GPT_BEARER_rot13 ?= fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj
GPT_TEMPERATURE ?= 0.7

# How to reach here from the current working directory
project.mk := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(project.mk)))))

# Where to make files
_$/BUILD := {build_dir}
$/BUILD :=$/$(_$/BUILD)

# The maker's home directory and name
H := $(shell echo ~)
I := $(shell whoami)

# Workaround Windows feature: Windows domain in whoami
I := $(subst \, ,$I)
ifneq ($(words $I),1)
    DOMAIN := $(firstword $(WHOAMI))
    I := $(lastword $I)
endif

# Workaround Windows WSL1 bug: Recursive make shell believes it is git bash on Windows
ifeq ($H,/Users/$I)
    H := /home/$I
endif

# A base PYTHON to use. It can be one of:
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

# A package manager for the PYTHON OS
ifndef !
    UNAME ?= $(PYTHON) $/{makemake_py}
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

# Define the rest here only once
ifndef $/PROJECT
ifeq (,$/)
    $/PROJECT := ./
else
    $/PROJECT := $/
endif
$/NAME ?= $(notdir $(realpath $/PROJECT))


### 
# Generic recipies for bringup, testing, reporting and auditing a project on any OS and CPU with PYTHON >= Python 3.7.
# Tested on x86 WSL1, x86 Windows and Arm64 MacOSX.

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:

# Make local commands available
PATHS := $(subst ;, ,$(subst :, ,$(PATH)))
ifeq (,$(filter .,$(PATHS)))
    .-ON-PATH := .-on-$(OS)-path
endif

# Notify the user if new rules were built and included, and make therefore restarted
ifeq (2,$(MAKE_RESTARTS))
    ifndef MAKER
        $(info # Hello $I, Welcome to makemake https://github.com/joakimbits/normalize)
    endif
    
    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $($/BUILD)
    $(info # $(PWD) $(filter-out $(INCLUDING)%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $/{makemake_py} $($/PYTHON) $($/BUILD))
    INCLUDED := $(MAKEFILE_LIST)
    INCLUDING := $($/BUILD)

    # Notify the user on abusage of make
    ifneq (0,$(MAKELEVEL))
        $(info # Warning: This is a recursive $(MAKE). Please use global variable names and include instead.)
        $(info # https://aegis.sourceforge.net/auug97.pdf)
        $(info # https://github.com/joakimbits/normalize/blob/main/example/Makefile)
    endif
endif

# Default rule
$/all: $/bringup

# Find all source files
$/SOURCE :=
$/MAKEFILE := $(wildcardproject.mk)
$/SOURCE += $($/MAKEFILE)
$/S := $(wildcard$/*.s)
$/SOURCE += $($/S)
$/C := $(wildcard$/*.c)
$/SOURCE += $($/C)
$/H := $(wildcard$/*.h)
$/SOURCE += $($/H)
$/CPP := $(wildcard$/*.cpp)
$/SOURCE += $($/CPP)
$/HPP := $(wildcard$/*.hpp)
$/SOURCE += $($/HPP)
$/PY := $(wildcard$/*.py)
$/PY := $(subst ./,$/,$($/PY))
$/SOURCE += $($/PY)
$/MD := $(wildcard$/*.md)
$/SOURCE += $($/MD)

# Find our git status
$/BRANCH := $(shell git branch --show-current)
$/BASELINE := $(shell git describe --match=v[0-9]* --always --tags --abbrev=0)
$/KNOWN := $(addprefix$/,$(shell cd $($/PROJECT) ; git ls-files . ':!:*/*'))
$/ADD := $(filter-out $($/KNOWN),$($/SOURCE))
$/MODIFIED := $(shell cd $($/PROJECT) && $(PYTHON) {makemake_py} --git-status . M)
$/REMOVE := $(filter-out $($/SOURCE),$($/KNOWN))

# Figure out where to checkout an old worktree
$/HOME_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/HOME := $($/HOME_DIR:./%=%)
$/NAME := $(notdir $(abspath $($/HOME_DIR)))
$/GIT_DIR := $(dir $(shell git rev-parse --git-common-dir))
$/HERE_DIR := $(shell $(PYTHON) $/{makemake_py} --relpath $($/GIT_DIR) $($/PROJECT))/
$/HERE := $($/HERE_DIR:%./=%)
$/OLD_WORKTREE := $($/HOME)$(_$/BUILD)$($/BASELINE)/$($/NAME)/
$/OLD := $($/OLD_WORKTREE)$($/HERE)

# Create status lines
ifeq ($(NORMAL),)
  NORMAL := `tput sgr0`
  RED := `tput setaf 1`
  GREEN := `tput setaf 2`
  YELLOW := `tput setaf 3`
  BLUE := `tput setaf 4`
  REVERSED := `tput rev`
endif

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

# List all installation and test targets
$/SRCS := $($/S)
$/CXX := $($/C)
$/CXX += $($/CPP)
$/SRCS += $($/CXX)
$/CODE := $($/SRCS)
$/CODE += $($/PY)

ifneq ($(strip $($/SRCS)),)
    $/EXE :=$/{_}
    $/EXE_TESTED := $($/BUILD){_}.tested
endif

$/BRINGUP := $($/PY: $/%=$($/BUILD)%.bringup)
$/TESTED := $($/EXE_TESTED)
$/TESTED += $($/PY: $/%=$($/BUILD)%.tested)
$/PRETESTED := $($/TESTED)
$/TESTED += $($/MD: $/%=$($/BUILD)%.sh-test.tested)

# Prepare for compilation
$/INC_DIRS := $($/PROJECT)
$/LDFLAGS := $(LDFLAGS)

ifneq ($(strip $($/S)),)
    $/LDFLAGS += -nostartfiles -no-pie
endif

$/CXXFLAGS := $($/LDFLAGS)
$/CXXFLAGS += -S $(addprefix -I,$($/INC_DIRS)) -MMD -MP
$/CFLAGS := $($/CXXFLAGS)
$/CXXFLAGS += $(CXXFLAGS)
$/CFLAGS += $(CFLAGS)
$/COBJS := $($/CXX: $/%=$($/BUILD)%.s)
$/DEPS := $($/COBJS:.s=.d)
$/OBJS := $($/S)
$/OBJS += $($/COBJS)
$/EXES := $($/EXE)
$/EXES += $($/PY)

# Prepare for bringup
$/PY_MK := $($/PY: $/%=$($/BUILD)%.mk)
$/DEPS += $($/PY_MK)

# Prepare for reporting
$/LOGIC := $($/MAKEFILE)
$/LOGIC += $($/CODE)
$/RESULT := $($/PY_MK)
$/RESULT += $($/BRINGUP)
$/RESULT += $($/TESTED)
$/REPORT := $($/BUILD)report-details.md
$/REPORT += $($/LOGIC: $/%=$($/BUILD)%.md)
$/REPORT += $($/RESULT:%=%.md)

# Convenience targets
.PHONY: $/bringup$/tested$/clean
$/bringup: $($/EXE) $($/BRINGUP)
$/tested: $($/TESTED)

# build/*.c.s: Compile C
$($/BUILD)%.c.s: $/%.c
	$(CXX) $($/CFLAGS) -c $< -o $@

# build/*.cpp.s: Compile C++
$($/BUILD)%.cpp.s: $/%.cpp
	$(CXX) $($/CXXFLAGS) -c $< -o $@

# Link executable
$/{_}: $($/OBJS)
	$(CC) $($/LDFLAGS) $^ -o $@

# Test executable:
$($/BUILD){_}.tested: $/{_}
	true | ./$< > $@ || (cat $@ && false)

# Check Python 3.9 syntax
$/syntax: $($/BUILD)syntax
$($/BUILD)%.py.syntax: $/%.py |$/venv/lib/python/site-packages/ruff
	$($/PYTHON) -m ruff --select=E9,F63,F7,F82 --target-version=py39 $< > $@ || (cat $@ && false)

# Install pip package in the local python:
$/venv/lib/python/site-packages/%: |$/venv/lib/python/site-packages
	$($/PYTHON) -m pip install $*

# Link to actual site-packages
$/venv/lib/python/site-packages: | $($/PYTHON)
	mkdir -p $(dir $@)
	ln -s $$(realpath --relative-to=$(dir $@) `venv/bin/python3 -c "import sys; print(sys.path[-1])"`) $@

# Workaround Windows python not installing #!venv/bin/python3
ifeq ($(PYTHON),/mnt/c/tools/miniconda3/python.exe)
    $/PYTHON_FINALIZE ?= && mkdir -p $(dir $@) && ln -s ../Scripts/python.exe $@
endif

# Setup a local python:
$($/PYTHON): | $(PYTHON) $(.-ON-PATH) $(SPEEDUP_WSL_DNS)
	( cd $($/PROJECT) && $(SPEEDUP_WSL_PIP)$(PYTHON) -m venv venv ) $($/PYTHON_FINALIZE)
	$(SPEEDUP_WSL_VENV)$(SPEEDUP_WSL_PIP)$($/PYTHON) -m pip install --upgrade pip
	$(SPEEDUP_WSL_PIP)$($/PYTHON) -m pip install requests  # Needed by -m makemake --prompt

# Install local commands before other commands
ifndef .-ON-PATH_TARGETS
    .-ON-PATH_TARGETS = 1
    %-on-Linux-path %-on-MacOSX-path: ~/.profile
	    echo 'export PATH="$*: $$PATH"' >> $< 
	    false # Please `source $<` or open a new shell to get $* on PATH, and retry `make $(MAKECMDGOALS)`.
    %-on-Windows-path:
	    $(call ps1,[System.Environment]::SetEnvironmentVariable('Path', '$*;' + [System.Environment]::GetEnvironmentVariable('Path', 'User'), 'User'))
endif

ifndef SPEEDUP_WSL_DNS_TARGET
    SPEEDUP_WSL_DNS_TARGET = 1
    $H/use_windows_dns.sh:
	    echo "# Fixing DNS issue in WSL https://gist.github.com/ThePlenkov/6ecf2a43e2b3898e8cd4986d277b5ecf#file-boot-sh" > $@                
	    echo -n "sed -i '/nameserver/d' /etc/resolv.conf && " >> $@
	    echo -n  "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command " >> $@
	    echo -n   "'(Get-DnsClientServerAddress -AddressFamily IPv4).ServerAddresses | " >> $@
	    echo -n    "ForEach-Object {{ \"nameserver \$$_\" }}' | tr -d '\\r' | " >> $@
	    echo "tee -a /etc/resolv.conf > /dev/null" >> $@
	    sudo sed -i '\|command=$@|d' /etc/wsl.conf
	    echo "command=$@" | sudo tee -a /etc/wsl.conf > /dev/null
	    sudo sh $@
endif

ifndef INSTALL_PIP_TARGET
    INSTALL_PIP_TARGET = 1
    $?/pip:
	    $! python3-pip
endif

# Check Python 3.9 style
$($/BUILD)%.py.style: $/%.py $($/BUILD)%.py.syntax
	$($/PYTHON) -m ruff --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Build a recipy for $($/BUILD)%.py.bringup
$($/BUILD)%.py.mk: $/%.py
	rm -f $@ && ( cd $($/PROJECT) && $(PYTHON) $*.py --generic --dep $(_$/BUILD)$*.py.mk ) ; [ -e $@ ] || echo "\$$($/BUILD)$*.py.bringup:; touch \$$@" >$@

# Check Python and command line usage examples in .py files
$($/BUILD)%.py.tested: $/%.py $($/BUILD)%.py.mk $($/BUILD)%.py.style $($/BUILD)%.py.bringup $($/EXE_TESTED) | $($/PYTHON)
	( cd $($/PROJECT) && $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$($/BUILD)%.sh-test.tested: $($/BUILD)%.sh-test $($/PRETESTED) |$/{makemake_py}
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $($/PROJECT) && $(PYTHON) {makemake_py} --timeout 60 --sh-test \
	    $(_$/BUILD)$*.sh-test ) > $$tmp && mv $$tmp $@
$($/BUILD)%.md.sh-test: $/%.md | $?/pandoc $?/jq
	pandoc -i $< -t json --preserve-tabs | jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && truncate -s -1 $@

# Document all source codes:
$/s: $($/SOURCE)
	@$(foreach s,$^,echo "___ $(s): ____" && cat $(s) ; )

# Document all assembly codes linked into$/{_}.
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
$/%.gfm: $($/BUILD)%.md
	pandoc --standalone -t $(patsubst .%,%,$(suffix $@)) -o $@ $^ \
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%an'`"
$/%.html$/%.pdf$/%.dzslides: $($/BUILD)%.md | \
  $?/pandoc $?/xelatex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	pandoc --standalone -t $(patsubst .%,%,$(suffix $@)) -o $@ $^ \
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%an'`" \
	       -V min-width=80%\!important -V geometry:margin=1in \
	       --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"

# Make a markdown document.
$/h :=\n---\n\n\#
$/~~~. =\\footnotesize\n~~~ {{$1}}
$/~~~sh :=$(call $/~~~.,.sh)
$/~~~ :=~~~\n\\normalsize\n
$($/BUILD)Makefile.md: project.mk
	( echo "$($/h)## [$*]($*)" && \
	  echo "$(call $/~~~.,.mk)" && \
	  cat $< && echo "$($/~~~)" ) >$@
$($/BUILD)%.md: $/%
	( echo "$($/h)## [$*]($*)" && \
	  echo "$(call $/~~~.,$(suffix $<))" && \
	  cat $< && echo "$($/~~~)" ) >$@
$($/BUILD)%.md: $($/BUILD)%
	( echo "$($/h)## [$*]($(_$/BUILD)$*)" && \
	  echo "$(call $/~~~.,$(suffix $<))" && \
	  cat $< && echo "$($/~~~)" ) >$@
$($/BUILD)%.bringup.md: $($/BUILD)%.bringup
	( echo "$($/h)## [$*]($(_$/BUILD)$*)" && \
	  echo "$($/~~~sh)" && \
	  cat $< && echo "$($/~~~)" ) >$@
$($/BUILD)%.tested.md: $($/BUILD)%.tested
	( echo "$($/h)## [$*]($(_$/BUILD)$*)" && \
	  echo "$($/~~~sh)" && \
	  cat $< && echo "$($/~~~)" ) >$@

# Report the project.
$/%: $/report.%
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/BRANCH_STATUS)"
$/slides: $/slides.html
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $($/BRANCH_STATUS)"
$/slides.html: $/report.dzslides
	mv $< $@
$/report.html$/report.pdf$/report.gfm \
 $/report.dzslides: $($/MD) $($/REPORT)
$/file = $(foreach _,$($/$1),[\`$_\`]($_))
$/exe = $(foreach _,$($/$1),[\`./$_\`]($_))
$/h_fixup :=sed -E '/^$$|[.]{{3}}/d'
$($/BUILD)report.md: $($/BUILD)report.txt
	echo "A build-here include-from-anywhere project \
based on [makemake](https://github.com/joakimbits/normalize)." > $@
	echo "\n- \`make report pdf html slides review audit\`" >> $@
ifneq ($(strip $($/EXE)),)
	echo "- \`./{_}\`: $(subst$/,,$(call $/file,SRCS))" >> $@
endif
ifneq ($(strip $($/PY)),)
	echo "- $(subst$/,,$(call $/exe,PY))" >> $@
endif
	echo "$($/h)## Installation" >> $@
	echo "$($/~~~sh)" >> $@
	echo "\$$ make" >> $@
	echo "$($/~~~)" >> $@
ifneq ($(strip $($/EXE)),)
	echo "- Installs \`./{_}\`." >> $@
endif
ifneq ($(strip $($/PY)),)
	echo "- Installs \`./venv\`." >> $@
	echo "- Installs $(subst$/,,$(call $/exe,PY))." >> $@
endif
ifneq ($($/EXES),)
	echo "$($/h)## Usage" >> $@
	echo "$($/~~~sh)" >> $@
	for x in $(subst $($/PROJECT),,$($/EXES)) ; do \
	  echo "\$$ true | ./$$x -h | $($/h_fixup)" >> $@ && \
	  ( cd $($/PROJECT) && true | ./$$x -h ) > $@.tmp && \
	  $($/h_fixup) $@.tmp >> $@ && rm $@.tmp ; \
	done
	echo >> $@
	echo "$($/~~~)" >> $@
	echo "$($/h)## Test" >> $@
	echo "$($/~~~sh)" >> $@
	echo "\$$ make tested" >> $@
	echo "$($/~~~)" >> $@
endif
ifneq ($(strip $($/EXE)),)
	echo "- Tests \`./{_}\`." >> $@
endif
ifneq ($(strip $($/PY)),)
	echo "- Verifies style and doctests in\
 $(subst $($/PROJECT),,$(call $/file,PY))." >> $@
endif
ifneq ($(strip $($/MD)),)
	echo "- Verifies doctests in $(subst $($/PROJECT),,$(call $/file,MD))." >> $@
endif
ifneq ($(strip $($/CODE)),)
	echo "$($/h)## Result" >> $@
	echo "$($/~~~sh)" >> $@
	echo "\$$ make report" >> $@
	( cd $($/PROJECT) && $(MAKE) report --no-print-directory ) >> $@
	echo "$($/~~~)" >> $@
	echo "\n---\n" >> $@
$($/BUILD)report-details.md:
	echo "$($/h)# Source code, installation and test result" >> $@
endif

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
$($/BUILD)audit.diff: $($/BUILD)prompt.diff | $($/PYTHON)
	cat $< > $@
	$($/PYTHON) -m makemake --prompt $< $(GPT_MODEL) $(GPT_TEMPERATURE) $(GPT_BEARER_rot13) >> $@
$($/BUILD)prompt.diff: $($/BUILD)review.diff
	$(PYTHON) $/{makemake_py} -c 'print(REVIEW)' > $@
	echo "$$ $(MAKE) $/review" >> $@
	cat $^ >> $@
	echo -n "$$ " >> $@
$($/BUILD)review.diff: $($/BUILD)files.diff $($/BUILD)comments.diff\
  $($/BUILD)report.diff
	cat $^ > $@
$($/BUILD)files.diff:
	echo "# $($/CHANGES_AUDIT)" > $@
$($/BUILD)comments.diff:
	echo "git --no-pager log --no-merges $($/BASELINE)..HEAD $($/PROJECT)" > $@
	git --no-pager log --no-merges $($/BASELINE)..HEAD $($/PROJECT) >> $@
$($/BUILD)report.diff: $($/OLD)report.gfm$/report.gfm
	echo "diff -u -U 100000 $< $(word 2,$^) | fold-unchanged" > $@
	( diff -u -U 100000 $< $(word 2,$^) | csplit -s - /----/ '{{*}}' && \
	  parts=`ls xx**` && \
	  changed_parts=`grep -l -e '^-' -e '^+' xx**` && \
	  for part in $$parts ; do \
	    if `echo "$$changed_parts" | fgrep -wq "$$part" \
	    || test "$$(wc $$part)" = "1"` ; then \
	      $(PYTHON) $/{makemake_py} --split $$part '\n \n \n' 's%02d' && \
	      sections=`ls s**` && \
	      changed_sections=`grep -l -e '^-' -e '^+' s**` && \
	      for section in $$sections ; do \
	        if `echo "$$changed_sections" | fgrep -wq "$$section" \
	        || test "$$(wc $$section)" = "1"` ; then \
	          $(PYTHON) $/{makemake_py} --split $$section '\n \n' 'p%02d' && \
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

# Include the autogenerated dependencies
$(info -include $($/DEPS))
-include $($/DEPS)
endif  # $/PROJECT
