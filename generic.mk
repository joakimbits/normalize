# {_}$ {" ".join(sys.argv)}
# {" ".join(sys.argv)} = Command used to generate this file
# {_} = project-name/src-directory
# {build_dir} = sub-directory-for-intermediate-files
# {makemake_py} = path-to-makemake.py

ifeq (,$(_{_}_DIR))

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
I := $(subst \, ,$I)
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
        ! ?= sudo apt update && sudo apt install -y
        ? ?= /usr/bin
        COUSINE ?= /usr/share/fonts/truetype/cousine
        CARLITO ?= /usr/share/fonts/truetype/crosextra
    endif
endif

# Make local commands available
PATHS := $(subst ;, ,$(subst :, ,$(PATH)))
ifeq (,$(filter .,$(PATHS)))
    .-ON-PATH := .-on-$(OS)-path
endif


### 
# Generic recipies for bringup, testing, reporting and auditing a project
# on any OS and CPU with PYTHON >= Python 3.7.
# Tested on WSL1 and bare Windows x86 and MacOSX Arm64.

# How to reach here from the current working directory
_{_}_Makefile := $(lastword $(MAKEFILE_LIST))
_{_} := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(_{_}_Makefile)))))
ifeq (,$(_{_}))
    _{_}_DIR := ./
else
    _{_}_DIR := $(_{_})
endif

# Where to build files
__{_}_BUILD := {build_dir}
_{_}_BUILD := $(_{_})$(__{_}_BUILD)

# The local python we bringup
__{_}_PYTHON := venv/$(VENV_PYTHON)
_{_}_PYTHON := $(_{_})$(__{_}_PYTHON)

# Notify the user if new rules were built and included, and make therefore restarted
ifeq ($(MAKE_RESTARTS),2)
    ifndef MAKER
        $(info # Hello $I, Welcome to makemake https://github.com/joakimbits/normalize)
    endif
    
    MAKER := $(shell $(MAKE) -v))
    INCLUDING ?= $(_{_}_BUILD)
    $(info # $(PWD) $(filter-out $(INCLUDING)%,$(subst $(INCLUDED),,$(MAKEFILE_LIST))) in $(word 6,$(MAKER)) $(wordlist 2,3,$(MAKER)) building $I `$(MAKE) $(MAKECMDGOALS)` on $(OS)-$(CPU) $(PYTHON) $(_{_}){makemake_py} $(_{_}_PYTHON) $(_{_}_BUILD))
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
_{_}_HOME := $(_{_}_HOME_DIR:./%=%)
_{_}_NAME := $(notdir $(abspath $(_{_}_HOME_DIR)))
_{_}_GIT_DIR := $(dir $(shell git rev-parse --git-common-dir))
_{_}_HERE_DIR := $(shell $(PYTHON) $(_{_}){makemake_py} --relpath $(_{_}_GIT_DIR) $(_{_}_DIR))/
_{_}_HERE := $(_{_}_HERE_DIR:%./=%)
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

ifeq ($(filter v%,$(_{_}_BASELINE)),)
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

_{_}_BRINGUP := $(_{_}_PY:$(_{_})%=$(_{_}_BUILD)%.bringup)
_{_}_TESTED := $(_{_}_EXE_TESTED)
_{_}_TESTED += $(_{_}_PY:$(_{_})%=$(_{_}_BUILD)%.tested)
_{_}_PRETESTED := $(_{_}_TESTED)
_{_}_TESTED += $(_{_}_MD:$(_{_})%=$(_{_}_BUILD)%.sh-test.tested)

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
_{_}_COBJS := $(_{_}_CXX:$(_{_})%=$(_{_}_BUILD)%.s)
_{_}_DEPS := $(_{_}_COBJS:.s=.d)
_{_}_OBJS := $(_{_}_S)
_{_}_OBJS += $(_{_}_COBJS)
_{_}_EXES := $(_{_}_EXE)
_{_}_EXES += $(_{_}_PY)

# Prepare for bringup
_{_}_PY_MK := $(_{_}_PY:$(_{_})%=$(_{_}_BUILD)%.mk)
_{_}_DEPS += $(_{_}_PY_MK)

# Prepare for reporting
_{_}_LOGIC := $(_{_}_MAKEFILE)
_{_}_LOGIC += $(_{_}_CODE)
_{_}_RESULT := $(_{_}_PY_MK)
_{_}_RESULT += $(_{_}_BRINGUP)
_{_}_RESULT += $(_{_}_TESTED)
_{_}_REPORT := $(_{_}_BUILD)report-details.md
_{_}_REPORT += $(_{_}_LOGIC:$(_{_})%=$(_{_}_BUILD)%.md)
_{_}_REPORT += $(_{_}_RESULT:%=%.md)

# Convenience targets
.PHONY: $(_{_})bringup $(_{_})tested $(_{_})clean
$(_{_})bringup: $(_{_}_EXE) $(_{_}_BRINGUP)
$(_{_})tested: $(_{_}_TESTED)

# build/*.c.s: Compile C
$(_{_}_BUILD)%.c.s: $(_{_})%.c
	$(CXX) $(_{_}_CFLAGS) -c $< -o $@

# build/*.cpp.s: Compile C++
$(_{_}_BUILD)%.cpp.s: $(_{_})%.cpp
	$(CXX) $(_{_}_CXXFLAGS) -c $< -o $@

# Link executable
$(_{_}){_}: $(_{_}_OBJS)
	$(CC) $(_{_}_LDFLAGS) $^ -o $@

# Test executable:
$(_{_}_BUILD){_}.tested: $(_{_}){_}
	true | ./$< > $@ || (cat $@ && false)

# Check Python 3.9 syntax
$(_{_})syntax: $(_{_}_BUILD)syntax
$(_{_}_BUILD)%.py.syntax: $(_{_})%.py | $(_{_})venv/lib/python/site-packages/ruff
	$(_{_}_PYTHON) -m ruff --select=E9,F63,F7,F82 --target-version=py39 $< > $@ || (cat $@ && false)

# Install pip package in the local python:
$(_{_})venv/lib/python/site-packages/%: | $(_{_})venv/lib/python/site-packages
	$(_{_}_PYTHON) -m pip install $*

# Link to actual site-packages
$(_{_})venv/lib/python/site-packages: | $(_{_}_PYTHON)
	mkdir -p $(dir $@)
	ln -s $$(realpath --relative-to=$(dir $@) `venv/bin/python3 -c "import sys; print(sys.path[-1])"`) $@

# Workaround Windows python not installing #!venv/bin/python3
ifeq ($(PYTHON),/mnt/c/tools/miniconda3/python.exe)
    _{_}_PYTHON_FINALIZE ?= && mkdir -p $(dir $@) && ln -s ../Scripts/python.exe $@
endif

# Setup a local python:
$(_{_}_PYTHON): | $(PYTHON) $(.-ON-PATH) $(SPEEDUP_WSL_DNS)
	( cd $(_{_}_DIR) && $(SPEEDUP_WSL_PIP)$(PYTHON) -m venv venv ) $(_{_}_PYTHON_FINALIZE)
	$(SPEEDUP_WSL_VENV)$(SPEEDUP_WSL_PIP)$(_{_}_PYTHON) -m pip install --upgrade pip
	$(SPEEDUP_WSL_PIP)$(_{_}_PYTHON) -m pip install requests  # Needed by -m makemake --prompt

# Install local commands before other commands
ifndef .-ON-PATH_TARGETS
    .-ON-PATH_TARGETS = 1
    %-on-Linux-path %-on-MacOSX-path: ~/.profile
	    echo 'export PATH="$*:$$PATH"' >> $< 
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
$(_{_}_BUILD)%.py.style: $(_{_})%.py $(_{_}_BUILD)%.py.syntax
	$(_{_}_PYTHON) -m ruff --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Build a recipy for $(_{_}_BUILD)%.py.bringup
$(_{_}_BUILD)%.py.mk: $(_{_})%.py
	rm -f $@ && ( cd $(_{_}_DIR) && $(PYTHON) $*.py --generic --dep $(__{_}_BUILD)$*.py.mk ) ; [ -e $@ ] || echo "\$$(_{_}_BUILD)$*.py.bringup:; touch \$$@" >$@

# Check Python and command line usage examples in .py files
$(_{_}_BUILD)%.py.tested: $(_{_})%.py $(_{_}_BUILD)%.py.mk $(_{_}_BUILD)%.py.style $(_{_}_BUILD)%.py.bringup $(_{_}_EXE_TESTED) | $(_{_}_PYTHON)
	( cd $(_{_}_DIR) && $*.py --test ) > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$(_{_}_BUILD)%.sh-test.tested: $(_{_}_BUILD)%.sh-test $(_{_}_PRETESTED) | $(_{_}){makemake_py}
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $(_{_}_DIR) && $(PYTHON) {makemake_py} --timeout 60 --sh-test \
	    $(__{_}_BUILD)$*.sh-test ) > $$tmp && mv $$tmp $@
$(_{_}_BUILD)%.md.sh-test: $(_{_})%.md | $?/pandoc $?/jq
	pandoc -i $< -t json --preserve-tabs | jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && truncate -s -1 $@

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
$(_{_})%.gfm: $(_{_}_BUILD)%.md
	pandoc --standalone -t $(patsubst .%,%,$(suffix $@)) -o $@ $^ \
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%an'`"
$(_{_})%.html $(_{_})%.pdf $(_{_})%.dzslides: $(_{_}_BUILD)%.md | \
  $?/pandoc $?/xelatex $(CARLITO)/Carlito-Regular.ttf $(COUSINE)/Cousine-Regular.ttf
	pandoc --standalone -t $(patsubst .%,%,$(suffix $@)) -o $@ $^ \
	       -M title="{_} $*" -M author="`git log -1 --pretty=format:'%an'`" \
	       -V min-width=80%\!important -V geometry:margin=1in \
	       --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"

# Make a markdown document.
_{_}_h :=\n---\n\n\#
_{_}~~~. =\\footnotesize\n~~~ {{$1}}
_{_}~~~sh :=$(call _{_}~~~.,.sh)
_{_}~~~ :=~~~\n\\normalsize\n
$(_{_}_BUILD)Makefile.md: $(_{_})Makefile
	( echo "$(_{_}_h)## [$*]($*)" && \
	  echo "$(call _{_}~~~.,.mk)" && \
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%.md: $(_{_})%
	( echo "$(_{_}_h)## [$*]($*)" && \
	  echo "$(call _{_}~~~.,$(suffix $<))" && \
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%.md: $(_{_}_BUILD)%
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \
	  echo "$(call _{_}~~~.,$(suffix $<))" && \
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%.bringup.md: $(_{_}_BUILD)%.bringup
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \
	  echo "$(_{_}~~~sh)" && \
	  cat $< && echo "$(_{_}~~~)" ) >$@
$(_{_}_BUILD)%.tested.md: $(_{_}_BUILD)%.tested
	( echo "$(_{_}_h)## [$*]($(__{_}_BUILD)$*)" && \
	  echo "$(_{_}~~~sh)" && \
	  cat $< && echo "$(_{_}~~~)" ) >$@

# Report the project.
$(_{_})%: $(_{_})report.%
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BRANCH_STATUS)"
$(_{_})slides: $(_{_})slides.html
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<)) $(_{_}_BRANCH_STATUS)"
$(_{_})slides.html: $(_{_})report.dzslides
	mv $< $@
$(_{_})report.html $(_{_})report.pdf $(_{_})report.gfm \
  $(_{_})report.dzslides: $(_{_}_MD) $(_{_}_REPORT)
_{_}_file = $(foreach _,$(_{_}_$1),[\`$_\`]($_))
_{_}_exe = $(foreach _,$(_{_}_$1),[\`./$_\`]($_))
_{_}_h_fixup :=sed -E '/^$$|[.]{{3}}/d'
$(_{_}_BUILD)report.md: $(_{_}_BUILD)report.txt
	echo "A build-here include-from-anywhere project \
based on [makemake](https://github.com/joakimbits/normalize)." > $@
	echo "\n- \`make report pdf html slides review audit\`" >> $@
ifneq ($(strip $(_{_}_EXE)),)
	echo "- \`./{_}\`: $(subst $(_{_}),,$(call _{_}_file,SRCS))" >> $@
endif
ifneq ($(strip $(_{_}_PY)),)
	echo "- $(subst $(_{_}),,$(call _{_}_exe,PY))" >> $@
endif
	echo "$(_{_}_h)## Installation" >> $@
	echo "$(_{_}~~~sh)" >> $@
	echo "\$$ make" >> $@
	echo "$(_{_}~~~)" >> $@
ifneq ($(strip $(_{_}_EXE)),)
	echo "- Installs \`./{_}\`." >> $@
endif
ifneq ($(strip $(_{_}_PY)),)
	echo "- Installs \`./venv\`." >> $@
	echo "- Installs $(subst $(_{_}),,$(call _{_}_exe,PY))." >> $@
endif
ifneq ($(_{_}_EXES),)
	echo "$(_{_}_h)## Usage" >> $@
	echo "$(_{_}~~~sh)" >> $@
	for x in $(subst $(_{_}_DIR),,$(_{_}_EXES)) ; do \
	  echo "\$$ true | ./$$x -h | $(_{_}_h_fixup)" >> $@ && \
	  ( cd $(_{_}_DIR) && true | ./$$x -h ) > $@.tmp && \
	  $(_{_}_h_fixup) $@.tmp >> $@ && rm $@.tmp ; \
	done
	echo >> $@
	echo "$(_{_}~~~)" >> $@
	echo "$(_{_}_h)## Test" >> $@
	echo "$(_{_}~~~sh)" >> $@
	echo "\$$ make tested" >> $@
	echo "$(_{_}~~~)" >> $@
endif
ifneq ($(strip $(_{_}_EXE)),)
	echo "- Tests \`./{_}\`." >> $@
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
	echo "\$$ make report" >> $@
	( cd $(_{_}_DIR) && $(MAKE) report --no-print-directory ) >> $@
	echo "$(_{_}~~~)" >> $@
	echo "\n---\n" >> $@
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
$(_{_})%: $(_{_}_BUILD)%.diff
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
	( diff -u -U 100000 $< $(word 2,$^) | csplit -s - /----/ '{{*}}' && \
	  parts=`ls xx**` && \
	  changed_parts=`grep -l -e '^-' -e '^+' xx**` && \
	  for part in $$parts ; do \
	    if `echo "$$changed_parts" | fgrep -wq "$$part" \
	    || test "$$(wc $$part)" = "1"` ; then \
	      $(PYTHON) $(_{_}){makemake_py} --split $$part '\n \n \n' 's%02d' && \
	      sections=`ls s**` && \
	      changed_sections=`grep -l -e '^-' -e '^+' s**` && \
	      for section in $$sections ; do \
	        if `echo "$$changed_sections" | fgrep -wq "$$section" \
	        || test "$$(wc $$section)" = "1"` ; then \
	          $(PYTHON) $(_{_}){makemake_py} --split $$section '\n \n' 'p%02d' && \
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
-include $(_{_}_DEPS)
endif  # _{_}_DIR
