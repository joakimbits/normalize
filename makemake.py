#!/usr/bin/python3
"""Print a Makefile for handling a python module and exit

Adds the following command line options to the main module:

--makemake: Print a Makefile.
--generic: Generalize so that any Makefile can include the Makefile.
--dep <file>: Create a Makefile for bringup of the module.

Makes it easy to add the following command line options to the parent module:

--test: Verify usage examples in the module and exit.
-c <string>: Execute a program string in the module and exit.


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

MAKEFILE_FROM_BUILD_DIR = f"""# $ {" ".join(sys.argv)}
ifeq ($(_{dir}_dir),) 

# Change to FORMAT=github within a github workflow
FORMAT := text

# Figure out where to find and build files
makefile_abspath := $(abspath $(lastword $(MAKEFILE_LIST)))
_{dir}_abspath := $(dir $(makefile_abspath))
_{dir} := $(subst $(PWD)/,,$(_{dir}_abspath))
__{dir}_build := %s
_{dir}_build := $(subst $(PWD)/,,$(_{dir}_abspath)$(__{dir}_build))
_{dir}_dir := ./$(_{dir})

# Find all source files
_{dir}_MD := $(wildcard $(_{dir})*.md)
_{dir}_S := $(wildcard $(_{dir})*.s)
_{dir}_C := $(wildcard $(_{dir})*.c)
_{dir}_CPP := $(wildcard $(_{dir})*.cpp)
_{dir}_PY := $(shell cd $(_{dir}_dir) && find . -maxdepth 1 -type f -name '*.py')
_{dir}_PY := $(subst ./,$(_{dir}),$(_{dir}_PY))
_{dir}_BRINGUP := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.bringup)
_{dir}_PY_TESTED := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.tested)
_{dir}_MD_TESTED := $(_{dir}_MD:$(_{dir})%%=$(_{dir}_build)%%.sh-test.tested)

# Prepare for compilation
_{dir}_SRCS := $(_{dir}_C) $(_{dir}_CPP)
_{dir}_OBJS := $(_{dir}_SRCS:$(_{dir})%%=$(_{dir}_build)%%.s)
_{dir}_DEPS += $(_{dir}_OBJS:.s=.mk)
_{dir}_OBJS += $(_{dir}_S)
_{dir}_INC_DIRS := $(_{dir}_dir)
_{dir}_INC_FLAGS := $(addprefix -I,$(_{dir}_INC_DIRS))
ifneq ($(strip $(_{dir}_S)),)
  _{dir}_EXE += $(_{dir}){dir}
  _{dir}_LDFLAGS += -nostartfiles
  _{dir}_LDFLAGS += -no-pie
  _{dir}_S_TESTED := $(_{dir}_build){dir}.tested
endif
_{dir}_CPPFLAGS := -S $(_{dir}_LDFLAGS) $(_{dir}_INC_FLAGS) -MMD -MP
_{dir}_TESTED := $(_{dir}_S_TESTED) $(_{dir}_PY_TESTED) $(_{dir}_MD_TESTED)

# Prepare for bringup
_{dir}_python := $(_{dir}_dir)venv/bin/python
_{dir}_DEPS := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.mk)

# Default rule
.DELETE_ON_ERROR:
$(_{dir})all: $(_{dir})bringup

$(_{dir})bringup: $(_{dir}_EXE) $(_{dir}_BRINGUP)
$(_{dir})tested: $(_{dir}_TESTED)

# Compile C
$(_{dir}_build)%%.c.s: $(_{dir})%%.c
	$(CXX) $(_{dir}_CPPFLAGS) $(CFLAGS) -c $< -o $@

# Compile C++
$(_{dir}_build)%%.cpp.s: $(_{dir})%%.cpp
	$(CXX) $(_{dir}_CPPFLAGS) $(CXXFLAGS) -c $< -o $@

# Link executable
$(_{dir}){dir}: $(_{dir}_OBJS)
	$(CC) $(_{dir}_LDFLAGS) $(LDFLAGS) $^ -o $@

# Test executable:
$(_{dir}_build){dir}.tested: $(_{dir}_dir){dir}
	$< > $@ || (cat $@ && false)

# Check Python 3.9 syntax
$(_{dir})syntax: $(_{dir}_build)syntax
$(_{dir}_build)syntax: $(_{dir}_PY) | $(_{dir})venv/bin/ruff
	$(_{dir}_python) -m ruff \\
	    --format=$(FORMAT) --select=E9,F63,F7,F82 \\
	    --target-version=py39 $(_{dir}_dir) > $@ || (cat $@ && false)
$(_{dir})venv/bin/ruff: | $(_{dir}_python)
	$(_{dir}_python) -m pip install ruff
$(_{dir})venv $(_{dir}_python):
	python3 -m venv $(_{dir})venv && $(_{dir}_python) -m pip install --upgrade pip

# Check Python 3.9 style
$(_{dir})style: $(_{dir}_build)style
$(_{dir}_build)style: $(_{dir}_build)syntax
	$(_{dir}_python) -m ruff --fix \\
	  --format=$(FORMAT) --target-version=py39 $(_{dir}_dir) > $@ || (cat $@ && false)

# Check Python and command line usage examples in .py files
$(_{dir}_build)%%.tested: $(_{dir})%% $(_{dir}_build)%%.mk $(_{dir}_build)%%.bringup \\
  $(_{dir}_build)style $(_{dir}_S_TESTED)
	$(_{dir}_python) $< --test > $@ || (cat $@ && false)
$(_{dir}_build)%%.py.mk: $(_{dir})%%.py
	cd $(_{dir}_dir) && python3 $*.py --generic --dep $(__{dir}_build)$*.py.mk
$(_{dir}_BRINGUP): $(_{dir}_EXE) $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.exe)
$(_{dir}_build)%%.exe: $(_{dir})%%
	chmod +x $< >$@

# Check command line usage examples in .md files
$(_{dir}_build)%%.sh-test.tested: $(_{dir}_build)%%.sh-test $(_{dir}_PY_TESTED) | \\
  $(_{dir})makemake.py
	( cd $(_{dir}_dir) && \\
	  ./makemake.py --timeout 60 --sh-test $(__{dir}_build)$*.sh-test ) >$@
$(_{dir}_build)%%.md.sh-test: $(_{dir})%%.md | /usr/bin/pandoc /usr/bin/jq
	pandoc -i $< -t json --preserve-tabs | \\
	jq -r -c '.blocks[] | select(.t | contains("CodeBlock"))? | .c | \
select(.[0][1][0] | contains("sh"))? | .[1]' > $@

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

# Make a pdf document.
$(_{dir})%%.pdf: $(_{dir}_build)%%.md | /usr/bin/pandoc /usr/bin/xelatex \\
  /usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf \\
  /usr/share/fonts/truetype/cousine/Cousine-Regular.ttf
	pandoc $^ -o $@ \\
	       -V geometry:margin=1in --pdf-engine=xelatex \\
	       --variable mainfont="Carlito" --variable monofont="Cousine"
ifndef pandoc
pandoc:=/usr/bin/pandoc
/usr/bin/pandoc:
	# Need a small general text processing framework: pandoc
	sudo apt install -y pandoc
/usr/bin/xelatex:
	# Need a modern pdf generation framework: xelatex
	sudo apt install -y texlive-xetex
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
$(_{dir}_build)Makefile.md: $(_{dir})Makefile
	( echo "## $<\\n\\\\\\footnotesize\\n~~~ {{.mk .numberLines}}" && \\
	  cat $< && echo "~~~\\n\\\\\\normalsize\\n" ) >$@
$(_{dir}_build)%%.md: $(_{dir})%%
	( echo "## $<\\n\\\\\\footnotesize\\n~~~ {{$(suffix $<) .numberLines}}" && \\
	  cat $< && echo "~~~\\n\\\\\\normalsize\\n" ) >$@
$(_{dir}_build)%%.md: $(_{dir}_build)%%
	( echo "## $<\\n\\\\\\footnotesize\\n~~~ {{$(suffix $<)}}" && \\
	  cat $< && echo "~~~\\n\\\\\\normalsize\\n" ) >$@
$(_{dir}_build)%%.bringup.md: $(_{dir}_build)%%.bringup
	( echo "## $<\\n\\\\\\footnotesize\\n~~~ {{.sh}}" && cat $< && \\
	  echo "~~~\\n\\\\\\normalsize\\n" ) >$@
$(_{dir}_build)%%.tested.md: $(_{dir}_build)%%.tested
	( echo "## $<" && cat $< )  | sed -z -e "s/\\n/\\n/g;s/\\n/\\n\\n/g" >$@

# Report the project.
_{dir}/* := $(_{dir})Makefile $(_{dir}_S) $(_{dir}_SRCS) $(_{dir}_PY)
_{dir}_build/* := $(_{dir}_DEPS) $(_{dir}_BRINGUP) $(_{dir}_TESTED)
_{dir}_report += $(_{dir}/*:$(_{dir})%%=$(_{dir}_build)%%.md)
_{dir}_report += $(_{dir}_build/*:%%=%%.md)
$(_{dir})pdf: $(_{dir})report.pdf
$(_{dir})report.pdf:: $(_{dir}_MD) $(_{dir}_report)
$(_{dir}_build)report.md:
	echo "# {dir} - an include-from-anywhere project" >$@

# Include the autogenerated dependencies
-include $(_{dir}_DEPS)
endif  # _{dir}_dir
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
                commands.append(([embed % command[2:] + end], [comment], []))
            elif command[:2] == '> ':
                if end:
                    command_lines[-1] = command_lines[-1][:-len(end)]
                command_lines.append(command[2:] + end)
                comment_lines.append(comment)
            elif command_lines and not output_lines and command_lines[-1][-1] == '\\':
                command_lines[-1] = command_lines[-1][:-len(end)]
                command_lines.append(embed % command + end)
                comment_lines.append(comment)
            elif command_lines and not pip:
                output_lines.append(command)
            elif command and pip:
                commands.append(([f"{pip} install " + command], [comment], []))

    return commands


def run_command_examples(commands, timeout=3):
    import subprocess

    for i, (command_lines, comment_lines, output_lines) in enumerate(commands):
        command = "\n".join(map("".join, zip(command_lines, comment_lines)))
        if module_dir:
            command = f"( cd {module_dir} && {command} )"
        output = "\n".join(output_lines)
        result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                timeout=timeout)
        assert not result.returncode, f"Example {i + 1} failed: $ {command}"
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
            python = f'$(_{dir}_python)'
            src_dir = f'$(_{dir})'
            build_dir = f'$(_{dir}_build)'
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
            embed = f"( cd $(_{dir}_dir) && %s"
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
        if bringups:
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
                bringup_rule += f" $(_{dir}_python)"
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
    """Doctest python examples in parent_module

    Test also command usage examples in this argparser epilog, and exit
    """
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
    """Test command usage examples in a file, and exit
    """
    def __call__(self, parser, args, values, option_string=None):
        try:
            examples = build_commands(open(values).read())
            run_command_examples(examples, args.timeout)
            print(f"All {len(examples)} command usage examples PASS")
        except AssertionError as err:
            print(err, file=sys.stderr)
            exit(1)

        exit(0)


class Command(Action):
    """Execute a program string and exit"""
    def __call__(self, parser, args, values, option_string=None):
        exec(values[0], parent_module.__dict__, locals())
        exit(0)


def add_arguments(argparser):
    argparser.add_argument('--makemake', action='store_true', help=(
        f"Print Makefile for {module_path}, and exit"))
    argparser.add_argument('--generic', action='store_true', help=(
        f"Print generic Makefile for {module_path}, and exit"))
    argparser.add_argument('--dep', action='store', help=(
        f"Build a {module}.dep target, print its Makefile include statement, and exit"))
    argparser.add_argument('--timeout', type=int, default=3, help=(
        "Test timeout in seconds (3)"))
    argparser.add_argument('--test', nargs=0, action=Test, help=(
        "Verify examples and exit"))
    argparser.add_argument('--sh-test', default=None, action=ShTest, help=(
        "Verify command examples in file and exit"))
    argparser.add_argument('-c', nargs=1, action=Command, help=(
        "Program passed in as string"))


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
	python3 -m pip install pip >> $@

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
