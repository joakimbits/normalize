#!/usr/bin/python3
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
            description=__doc__,
            epilog='''Examples:
    $ echo hello world''')

        makemake.add_arguments(argparser)
        args = argparser.parse_args()

Dependencies:
$ python3 -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version'
pip  # Fake module dependency
"""

import sys
import os
import re
from argparse import Action


parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
dir = os.path.split(os.getcwd())[1]
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
after the (first) --- below. There I used the command `$ make changes` which prints 
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

MAKEFILE_FROM_BUILD_DIR = f"""# $ {" ".join(sys.argv)}
ifeq ($(_{dir}_DIR),) 

# A large-context openai model suitable for code review
_{dir}_MODEL := gpt-3.5-turbo-16k

# A temperature for the openai continuation.
_{dir}_TEMPERATURE = 0.7

# A rot13 encoded openai Bearer key
_{dir}_BEARER_rot13 := fx-ZyOYgw6hQnfZ5Shey79vG3OyoxSWtuyB30oAOhe3M33ofaPj

# Change to _{dir}_FORMAT=github within a github workflow
_{dir}_FORMAT := text

# Figure out where to find and build files
_{dir}_THIS_MAKEFILE_ABSPATH := $(abspath $(lastword $(MAKEFILE_LIST)))
_{dir}_ABSPATH := $(dir $(_{dir}_THIS_MAKEFILE_ABSPATH))
_{dir} := $(subst $(PWD)/,,$(_{dir}_ABSPATH))
__{dir}_BUILD := %s
_{dir}_BUILD := $(subst $(PWD)/,,$(_{dir}_ABSPATH)$(__{dir}_BUILD))
ifeq ($(_{dir}),)
  _{dir}_DIR := ./
else
  _{dir}_DIR := $(_{dir})
endif

# Find all source files
_{dir}_S := $(wildcard $(_{dir})*.s)
_{dir}_C := $(wildcard $(_{dir})*.c)
_{dir}_CPP := $(wildcard $(_{dir})*.cpp)
_{dir}_PY := $(shell cd $(_{dir}_DIR) && find . -maxdepth 1 -type f -name '*.py')
_{dir}_PY := $(subst ./,$(_{dir}),$(_{dir}_PY))
_{dir}_MD := $(wildcard $(_{dir})*.md)

# List all installation and test targets
_{dir}_SRCS := $(_{dir}_S)
_{dir}_CXX := $(_{dir}_C)
_{dir}_CXX += $(_{dir}_CPP)
_{dir}_SRCS += $(_{dir}_CXX)
_{dir}_CODE := $(_{dir}_SRCS)
_{dir}_CODE += $(_{dir}_PY)
ifneq ($(strip $(_{dir}_SRCS)),)
  _{dir}_EXE := $(_{dir}){dir}
  _{dir}_EXE_TESTED := $(_{dir}_BUILD){dir}.tested
endif
_{dir}_BRINGUP := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_BUILD)%%.bringup)
_{dir}_TESTED := $(_{dir}_EXE_TESTED)
_{dir}_TESTED += $(_{dir}_PY:$(_{dir})%%=$(_{dir}_BUILD)%%.tested)
_{dir}_TESTED += $(_{dir}_MD:$(_{dir})%%=$(_{dir}_BUILD)%%.sh-test.tested)

# Prepare for compilation
_{dir}_INC_DIRS := $(_{dir}_DIR)
_{dir}_LDFLAGS := $(LDFLAGS)
ifneq ($(strip $(_{dir}_S)),)
  _{dir}_LDFLAGS += -nostartfiles -no-pie
endif
_{dir}_CXXFLAGS := $(_{dir}_LDFLAGS)
_{dir}_CXXFLAGS += -S $(addprefix -I,$(_{dir}_INC_DIRS)) -MMD -MP
_{dir}_CFLAGS := $(_{dir}_CXXFLAGS)
_{dir}_CXXFLAGS += $(CXXFLAGS)
_{dir}_CFLAGS += $(CFLAGS)
_{dir}_COBJS := $(_{dir}_CXX:$(_{dir})%%=$(_{dir}_BUILD)%%.s)
_{dir}_DEPS := $(_{dir}_COBJS:.s=.d)
_{dir}_OBJS := $(_{dir}_S)
_{dir}_OBJS += $(_{dir}_COBJS)
_{dir}_EXES := $(_{dir}_EXE)
_{dir}_EXES += $(_{dir}_PY)

# Prepare for bringup
_{dir}_PYTHON := $(_{dir}_DIR)venv/bin/python
_{dir}_PY_MK := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_BUILD)%%.mk)
_{dir}_DEPS += $(_{dir}_PY_MK)

# Prepare for reporting
_{dir}_LOGIC := $(_{dir})Makefile
_{dir}_LOGIC += $(_{dir}_CODE)
_{dir}_RESULT := $(_{dir}_PY_MK)
_{dir}_RESULT += $(_{dir}_BRINGUP)
_{dir}_RESULT += $(_{dir}_TESTED)
_{dir}_REPORT := $(_{dir}_BUILD)report-details.md
_{dir}_REPORT += $(_{dir}_LOGIC:$(_{dir})%%=$(_{dir}_BUILD)%%.md)
_{dir}_REPORT += $(_{dir}_RESULT:%%=%%.md)

# Default rule
.DELETE_ON_ERROR:
$(_{dir})all: $(_{dir})bringup

$(_{dir})bringup: $(_{dir}_EXE) $(_{dir}_BRINGUP)
$(_{dir})tested: $(_{dir}_TESTED)

# build/*.c.s: Compile C
$(_{dir}_BUILD)%%.c.s: $(_{dir})%%.c
	$(CXX) $(_{dir}_CFLAGS) -c $< -o $@

# build/*.cpp.s: Compile C++
$(_{dir}_BUILD)%%.cpp.s: $(_{dir})%%.cpp
	$(CXX) $(_{dir}_CXXFLAGS) -c $< -o $@

# Link executable
$(_{dir}){dir}: $(_{dir}_OBJS)
	$(CC) $(_{dir}_LDFLAGS) $^ -o $@

# Test executable:
$(_{dir}_BUILD){dir}.tested: $(_{dir}){dir}
	./$< > $@ || (cat $@ && false)

# Check Python 3.9 syntax
$(_{dir})syntax: $(_{dir}_BUILD)syntax
$(_{dir}_BUILD)syntax: $(_{dir}_PY) | $(_{dir})venv/bin/ruff
	$(_{dir}_PYTHON) -m ruff \\
	    --format=$(_{dir}_FORMAT) --select=E9,F63,F7,F82 \\
	    --target-version=py39 $(_{dir}_DIR) > $@ || (cat $@ && false)
$(_{dir})venv/bin/ruff: | $(_{dir}_PYTHON)
	$(_{dir}_PYTHON) -m pip install ruff
$(_{dir})venv $(_{dir}_PYTHON):
	python3 -m venv $(_{dir})venv && $(_{dir}_PYTHON) -m pip install --upgrade pip

# Check Python 3.9 style
$(_{dir})style: $(_{dir}_BUILD)style
$(_{dir}_BUILD)style: $(_{dir}_BUILD)syntax
	$(_{dir}_PYTHON) -m ruff --fix \\
	  --format=$(_{dir}_FORMAT) --target-version=py39 $(_{dir}_DIR) > $@ \\
	|| (cat $@ && false)

# Build a recipy for $(_{dir}_BUILD)%%.py.bringup
$(_{dir}_BUILD)%%.py.mk: $(_{dir})%%.py
	cd $(_{dir}_DIR) && python3 $*.py --generic --dep $(__{dir}_BUILD)$*.py.mk

# Check Python and command line usage examples in .py files
$(_{dir}_BUILD)%%.py.tested: $(_{dir})%%.py $(_{dir}_BUILD)%%.py.mk \\
  $(_{dir}_BUILD)style $(_{dir}_BUILD)%%.py.bringup $(_{dir}_EXE_TESTED)
	$(_{dir}_PYTHON) $< --test > $@ || (cat $@ && false)

# Check command line usage examples in .md files
$(_{dir}_BUILD)%%.sh-test.tested: $(_{dir}_BUILD)%%.sh-test $(_{dir}_PY_TESTED) | \\
  $(_{dir})makemake.py
	tmp=$@-$$(if [ -e $@-0 ] ; then echo 1 ; else echo 0 ; fi) && \
	( cd $(_{dir}_DIR) && ./makemake.py --timeout 60 --sh-test \
	    $(__{dir}_BUILD)$*.sh-test ) > $$tmp && mv $$tmp $@
$(_{dir}_BUILD)%%.md.sh-test: $(_{dir})%%.md | /usr/bin/pandoc /usr/bin/jq
	pandoc -i $< -t json --preserve-tabs | \
	jq -r '.blocks[] | select(.t | contains("CodeBlock"))? | .c | \
select(.[0][1][0] | contains("sh"))? | .[1]' > $@ && \\
	truncate -s -1 $@

.PHONY: $(_{dir})s $(_{dir})a $(_{dir})d $(_{dir})b $(_{dir})report

# Document all source codes:
$(_{dir})s: $(_{dir}_S) $(_{dir}_SRCS)
	@$(foreach s,$^,echo "___ $(s): ____" && cat $(s) ; )

# Document all assembly codes linked into $(_{dir}){dir}.
$(_{dir})a: $(_{dir}_OBJS)
	@$(foreach a,$^,echo "___ $(a): ____" && cat $(a) ; )

# Document all dependencies.
$(_{dir})d: $(_{dir}_DEPS)
	@$(foreach d,$^,echo "___ $(d): ____" && cat $(d) ; )

# Document all bringups.
$(_{dir})b: $(_{dir}_BRINGUP)
	@$(foreach b,$^,echo "___ $(b) ____" && cat $(b) ; )

# Document all test results.
$(_{dir})report: $(_{dir}_TESTED)
	@$(foreach t,$^,echo "___ $(t): ____" && cat $(t) ; )

# Make a standalone html, pdf, gfm or dzslides document.
$(_{dir})%%.html $(_{dir})%%.pdf $(_{dir})%%.gfm $(_{dir})%%.dzslides: \\
  $(_{dir}_BUILD)%%.md | \\
  /usr/bin/pandoc /usr/bin/xelatex \\
  /usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf \\
  /usr/share/fonts/truetype/cousine/Cousine-Regular.ttf
	pandoc --standalone -t $(patsubst .%%,%%,$(suffix $@)) -o $@ $^ \\
	       -M title="{dir} $*" -M author="`git log -1 --pretty=format:'%%an'`" \\
	       -V min-width=80%%\!important -V geometry:margin=1in \\
	       --pdf-engine=xelatex -V mainfont="Carlito" -V monofont="Cousine"
ifndef pandoc
pandoc:=/usr/bin/pandoc
# Make doesn't detect /usr/bin/pandoc: A phony target that may actually exist.
/usr/bin/pandoc: pandoc-3.1.6.1-1-amd64.deb
	@if [ ! -e /usr/bin/pandoc ] ; then (sudo dpkg -i $< ) ; fi
pandoc-%%-1-amd64.deb:
	@if [ ! -e /usr/bin/pandoc ] ; then ( \\
	  echo "Need a small general text processing framework: pandoc" && \\
	  wget https://github.com/jgm/pandoc/releases/download/$*/pandoc-$*-1-amd64.deb \\
	) ; fi
/usr/bin/xelatex:
	# Need a modern pdf generation framework: xelatex
	sudo apt-get update && sudo apt install -y texlive-xetex
/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf:
	# Need a more screen-readable normal font: carlito
	sudo apt-get install fonts-crosextra-carlito
/usr/share/fonts/truetype/cousine/Cousine-Regular.ttf:
	# Need a more screen-readable fixed-size font: cousine
	( sudo mkdir -p $(dir $@) && cd $(dir $@) && \\
	  fonts=https://raw.githubusercontent.com/google/fonts/main/apache && \\
	  sudo wget $$fonts/cousine/DESCRIPTION.en_us.html && \\
	  sudo wget $$fonts/cousine/Cousine-Bold.ttf && \\
	  sudo wget $$fonts/cousine/Cousine-BoldItalic.ttf && \\
	  sudo wget $$fonts/cousine/Cousine-Italic.ttf && \\
	  sudo wget $$fonts/cousine/Cousine-Regular.ttf )
/usr/bin/jq:
	# Need a tool to filter json: jq
	sudo apt install -y jq
endif

# Make a markdown document.
_{dir}_h :=\\n---\\n\\n\#
_{dir}~~~. =\\\\\\footnotesize\\n~~~ {{$1}}
_{dir}~~~sh :=$(call _{dir}~~~.,.sh)
_{dir}~~~ :=~~~\\n\\\\\\normalsize\\n
$(_{dir}_BUILD)Makefile.md: $(_{dir})Makefile
	( echo "$(_{dir}_h)## [$(subst $(_{dir}),,$<)]($<)" && \\
	  echo "$(call _{dir}~~~.,.mk)" && \\
	  cat $< && echo "$(_{dir}~~~)" ) >$@
$(_{dir}_BUILD)%%.md: $(_{dir})%%
	( echo "$(_{dir}_h)## [$(subst $(_{dir}),,$<)]($<)" && \\
	  echo "$(call _{dir}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{dir}~~~)" ) >$@
$(_{dir}_BUILD)%%.md: $(_{dir}_BUILD)%%
	( echo "$(_{dir}_h)## [$(subst $(_{dir}),,$<)]($<)" && \\
	  echo "$(call _{dir}~~~.,$(suffix $<))" && \\
	  cat $< && echo "$(_{dir}~~~)" ) >$@
$(_{dir}_BUILD)%%.bringup.md: $(_{dir}_BUILD)%%.bringup
	( echo "$(_{dir}_h)## [$(subst $(_{dir}),,$<)]($<)" && \\
	  echo "$(_{dir}~~~sh)" && \\
	  cat $< && echo "$(_{dir}~~~)" ) >$@
$(_{dir}_BUILD)%%.tested.md: $(_{dir}_BUILD)%%.tested
	( echo "$(_{dir}_h)## [$(subst $(_{dir}),,$<)]($<)" && \\
	  echo "$(_{dir}~~~sh)" && \\
	  cat $< && echo "$(_{dir}~~~)" ) >$@

# Report the project.
$(_{dir})%%: $(_{dir})report.%%
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<))"
$(_{dir})slides: $(_{dir})slides.html
	@echo "# file://$(subst /mnt/c/,/C:/,$(realpath $<))"
$(_{dir})slides.html: $(_{dir})report.dzslides
	mv $< $@
$(_{dir})report.html $(_{dir})report.pdf $(_{dir})report.gfm \\
  $(_{dir})report.dzslides: $(_{dir}_MD) $(_{dir}_REPORT)
_{dir}_file = $(foreach _,$(_{dir}_$1),[\\`$_\\`]($_))
_{dir}_exe = $(foreach _,$(_{dir}_$1),[\\`./$_\\`]($_))
_{dir}_h_fixup :=sed -E '/^$$|[.]{{3}}/d'
$(_{dir}_BUILD)report.md: $(_{dir}_TESTED)
	echo "A build-here include-from-anywhere project \
based on [makemake](https://github.com/joakimbits/normalize)." > $@
	echo "\\n- \\`make report pdf html slides review audit\\`" >> $@
ifneq ($(strip $(_{dir}_EXE)),)
	echo "- \\`./{dir}\\`: $(subst $(_{dir}),,$(call _{dir}_file,SRCS))" >> $@
endif
ifneq ($(strip $(_{dir}_PY)),)
	echo "- $(subst $(_{dir}),,$(call _{dir}_exe,PY))" >> $@
endif
	echo "$(_{dir}_h)## Installation" >> $@
	echo "$(_{dir}~~~sh)" >> $@
	echo "\\$$ make" >> $@
	echo "$(_{dir}~~~)" >> $@
ifneq ($(strip $(_{dir}_EXE)),)
	echo "- Installs \\`./{dir}\\`." >> $@
endif
ifneq ($(strip $(_{dir}_PY)),)
	echo "- Installs \\`./venv\\`." >> $@
	echo "- Installs $(subst $(_{dir}),,$(call _{dir}_exe,PY))." >> $@
endif
ifneq ($(_{dir}_EXES),)
	echo "$(_{dir}_h)## Usage" >> $@
	echo "$(_{dir}~~~sh)" >> $@
	for x in $(subst $(_{dir}_DIR),,$(_{dir}_EXES)) ; do \\
	  echo "\\$$ ./$$x -h | $(_{dir}_h_fixup)" >> $@ && \\
	  ( cd $(_{dir}_DIR) && ./$$x -h ) > $@.tmp && \\
	  $(_{dir}_h_fixup) $@.tmp >> $@ && rm $@.tmp ; \\
	done
	echo >> $@
	echo "$(_{dir}~~~)" >> $@
	echo "$(_{dir}_h)## Test" >> $@
	echo "$(_{dir}~~~sh)" >> $@
	echo "\\$$ make tested" >> $@
	echo "$(_{dir}~~~)" >> $@
endif
ifneq ($(strip $(_{dir}_EXE)),)
	echo "- Tests \\`./{dir}\\`." >> $@
endif
ifneq ($(strip $(_{dir}_PY)),)
	echo "- Verifies style and doctests in\
 $(subst $(_{dir}_DIR),,$(call _{dir}_file,PY))." >> $@
endif
ifneq ($(strip $(_{dir}_MD)),)
	echo "- Verifies doctests in $(subst $(_{dir}_DIR),,$(call _{dir}_file,MD))." >> $@
endif
ifneq ($(strip $(_{dir}_CODE)),)
	echo "$(_{dir}_h)## Result" >> $@
	echo "$(_{dir}~~~sh)" >> $@
	echo "\\$$ make report" >> $@
	( cd $(_{dir}_DIR) && $(MAKE) report --no-print-directory ) >> $@
	echo "$(_{dir}~~~)" >> $@
	echo "\\n---\\n" >> $@
$(_{dir}_BUILD)report-details.md:
	echo "$(_{dir}_h)# Source code, installation and test result" >> $@
endif

# Document last release.
$(_{dir})old: $(_{dir}_BUILD)tagged $(_{dir}_BUILD)old_report.gfm
	cat $<
	cat -n $(word 2,$^)
$(_{dir}_BUILD)old_report.gfm: $(_{dir}_BUILD)tagged $(_{dir}_BUILD)branch
	echo `mktemp -d`/new > $@.tmpdir
	mkdir -p `cat $@.tmpdir`
	cp -a $(_{dir}_DIR)* `cat $@.tmpdir`
	git checkout --detach $$(cat $<)
	rm -rf $(_{dir})venv
	$(MAKE) $(_{dir})report.gfm --no-print-directory
	mv $(_{dir})report.gfm `cat $@.tmpdir`/$(__{dir}_BUILD)old_report.gfm
	git checkout $$(cat $(word 2,$^))
	new=`cat $@.tmpdir` && rm -r $(_{dir}_DIR)* && mv $$new/* $(_{dir}_DIR)
	rm -rf `cat $@.tmpdir`
$(_{dir}_BUILD)tagged:
	git describe --tags --abbrev=0 > $@
$(_{dir}_BUILD)branch:
	git branch --show-current > $@

# Document changes since last release.
$(_{dir})changes: $(_{dir}_BUILD)old_report.gfm $(_{dir})report.gfm\
 | $(_{dir})tag $(_{dir})change_comments $(_{dir})project_changes
$(_{dir})tag: $(_{dir}_BUILD)tagged
	cat $<
$(_{dir})change_comments: $(_{dir}_BUILD)tagged
	git --no-pager log --no-merges $$(cat $(_{dir}_BUILD)tagged)..HEAD $(_{dir}_DIR)
$(_{dir})project_changes: $(_{dir}_BUILD)old_report.gfm $(_{dir})report.gfm
	# Unified diff of project report changes:
	@( diff -u -U 100000 $< $(word 2,$^) | csplit -s - /----/ '{{*}}' && \\
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
	  rm xx**; )

# Prompt for a release review.
$(_{dir})review: $(_{dir}_BUILD)prompt
	@cat $<
$(_{dir}_BUILD)prompt: $(_{dir}_BUILD)context
	python3 -m makemake -c 'print(REVIEW)' > $@
	cat $< >> $@
$(_{dir}_BUILD)context: $(_{dir}_BUILD)old_report.gfm $(_{dir})report.gfm
	echo '$$ $(MAKE) $(_{dir})changes' > $@
	$(MAKE) $(_{dir})changes --no-print-directory >> $@
	echo -n '$$ ' >> $@

# Use GPT for a release review.
$(_{dir})audit: $(_{dir}_BUILD)prompt
	python3 -m makemake --prompt $< $(_{dir}_MODEL) $(_{dir}_TEMPERATURE)\
 $(_{dir}_BEARER_rot13)

# Include the autogenerated dependencies
-include $(_{dir}_DEPS)
endif  # _{dir}_DIR
"""  # noqa: E101

COMMENT_GROUP_PATTERN = re.compile("(\s*#.*)?$")


def make_rule(rule, commands, file=sys.stdout):
    print(rule, file=file)
    print('\t' + " \\\n\t".join(commands), file=file)


def build_commands(doc, heading=None, embed="%s", end="", pip=""):
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
                prefix = dir + "/"
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
            python = f'$(_{dir}_PYTHON)'
            src_dir = f'$(_{dir})'
            build_dir = f'$(_{dir}_BUILD)'
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
            embed = f"( cd $(_{dir}_DIR) && %s"
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
                bringup_rule += f" $(_{dir}_PYTHON)"
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
        description=__doc__,
        epilog="""Examples:
$ python3 makemake.py --dep makemake.dep
include makemake.dep

$ cat makemake.dep
makemake.py.bringup: makemake.py makemake.dep
	python3 -c 'import sys; assert sys.version_info[:2] >= (3, 7), sys.version' > $@"""
               """ && \\
	python3 -m pip install pip >> $@ && \\
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
