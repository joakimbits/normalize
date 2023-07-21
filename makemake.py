"""Print a Makefile for handling a python module and exit

Adds the following command line options:

--makemake: Print a Makefile.

--generic: Generalize so that any Makefile can include the Makefile.

--dep <file>: Create a make file for just the bringup of a module.

--test: Verify usage examples in the module and exit.

Only the last command requires argparser.parse_args() as in the Usage section below.


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
$ python3 -c 'import sys; assert sys.version_info[:2] >= (3, 9), sys.version'
pip  # Fake module dependency
"""

import sys
import os
import re
from argparse import Action


parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
dir = os.path.split(os.path.split(parent_module.__file__)[0])[1]
module_path = sys.argv[0]
module_dir, module_py = os.path.split(module_path)
module, ext = os.path.splitext(module_py)

MAKEFILE_FROM_BUILD_DIR = f"""# $ {" ".join(sys.argv)}
# Change to FORMAT=github within a github workflow
FORMAT := text

# Figure out where to find and build files
makefile_abspath := $(abspath $(lastword $(MAKEFILE_LIST)))
_{dir}_abspath := $(dir $(makefile_abspath))
_{dir} := $(subst $(PWD)/,,$(_{dir}_abspath))
_{dir}_build := $(subst $(PWD)/,,$(_{dir}_abspath)%s)
ifeq ($(_{dir}),)
  _{dir}_dir := ./
else
  _{dir}_dir := $(_{dir})
endif
_{dir}_python = $(_{dir}_dir)venv/bin/python

# Find all the Python files
_{dir}_PY := $(wildcard $(_{dir})*.py)

# List the make, test and tested targets for Python files
_{dir}_DEPS := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.d)
_{dir}_BRINGUPS := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.bringup)
_{dir}_TESTEDS := $(_{dir}_PY:$(_{dir})%%=$(_{dir}_build)%%.tested)

# Default rule
.DELETE_ON_ERROR:
.PHONY: $(_{dir})all
$(_{dir})all: $(_{dir})style $(_{dir}_TESTEDS)

# Auto-generated python dependencies.
# Each .d here makes one $(_{dir}_build)%%.py.bringup within a common local python venv.
# Note: Any conflicts between bringups are just ignored: The last bringup wins.
# If that is a problem, split this {dir} into separate directories with different venvs.
$(_{dir})venv $(_{dir}_python): | $(_{dir})makemake.py
	python3 -m venv $(_{dir})venv && $(_{dir}_python) -m pip install --upgrade pip
$(_{dir}_build)%%.py.d: $(_{dir})%%.py
	python3 $< --generic --dep $@

# Check Python 3.9 syntax
$(_{dir})syntax: $(_{dir}_PY) | $(_{dir})venv/bin/ruff
	$(_{dir}_python) -m ruff \\
	    --format=$(FORMAT) --select=E9,F63,F7,F82 \\
	    --target-version=py39 $(_{dir}_dir) > $@ || (cat $@ && false)
$(_{dir})venv/bin/ruff: | $(_{dir}_python)
	$(_{dir}_python) -m pip install ruff

# Check Python 3.9 style
$(_{dir})style: $(_{dir})syntax
	$(_{dir}_python) -m ruff --fix \\
	  --format=$(FORMAT) --target-version=py39 $(_{dir}_dir) > $@ || (cat $@ && false)

# Check usage examples
$(_{dir}_build)%%.tested: $(_{dir})%% $(_{dir}_build)%%.d $(_{dir}_build)%%.bringup \\
  | $(_{dir}_python)
	$(_{dir}_python) $< --test > $@

# Find all the C, C++ and ASM source files
_{dir}_SRC := $(shell find $(_{dir}_dir) -name '*.cpp' -or -name '*.c' -or -name '*.s')

# List the wanted binaries and their build dependencies
_{dir}_OBJS := $(_{dir}_SRCS:$(_{dir}_dir)%%.c=$(_{dir}_build_dir)%%.c.o)
_{dir}_OBJS += $(_{dir}_SRCS:$(_{dir}_dir)%%.cpp=$(_{dir}_build_dir)%%.cpp.o)
_{dir}_DEPS += $(_{dir}_OBJS:.o=.d)
_{dir}_INC_DIRS := $(shell find $(_{dir}_dir) -type d)
_{dir}_INC_FLAGS := $(addprefix -I,$(_{dir}_INC_DIRS))
_{dir}_CPPFLAGS := $(_{dir}_INC_FLAGS) -MMD -MP

# The final executable links all the binaries
$(_{dir}_build_dir)_{dir}: $(_{dir}_OBJS)
	$(CXX) $(_{dir}_OBJS) -o $@ $(LDFLAGS)

$(_{dir}_build_dir)%%.c.o: $(_{dir}_dir)%%.c
	mkdir -p $(dir $@)
	$(CC) $(_{dir}_CPPFLAGS) $(CFLAGS) -c $< -o $@

$(_{dir}_build_dir)%%.cpp.o: $(_{dir}_dir)%%.cpp
	mkdir -p $(dir $@)
	$(CXX) $(_{dir}_CPPFLAGS) $(CXXFLAGS) -c $< -o $@

# Include all build dependencies
-include $(_{dir}_DEPS)
"""  # noqa: E101

COMMENT_GROUP_PATTERN = re.compile("(\s*#.*)?$")


def make_rule(rule, commands, file=sys.stdout):
    print(rule, file=file)
    print('\t' + " \\\n\t".join(commands), file=file)


def build_commands(doc, heading, embed="%s", end="", pip=""):
    before_after = doc.split(f"{heading}\n", maxsplit=1)
    commands = []
    if len(before_after) >= 2:
        for line in before_after[1].split('\n'):
            command_lines, comment_lines, output_lines = (
                commands[-1] if commands else ([], [], []))
            command, comment, _ = re.split(COMMENT_GROUP_PATTERN, line, maxsplit=1)
            if comment is None:
                comment = ""
            if command[:2] == '$ ':
                commands.append(([embed % command[2:] + end], [comment], []))
            elif command[:2] == '> ':
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


def run_command_examples(commands):
    import subprocess

    for i, (command_lines, comment_lines, output_lines) in enumerate(commands):
        command = "\n".join(command_lines)
        if module_dir:
            command = f"( cd {module_dir} && {command} )"
        output = "\n".join(output_lines)
        result = subprocess.run(command, shell=True, capture_output=True, text=True,
                                timeout=3)
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
                dep_dir = (dep_dir + "/").removeprefix(dir + "/")
        else:
            dep_dir_now = dep_dir = 'build/'
            dep_filename = f'{module_py}.d'
            dep_file = f'build/{module_py}.d'

        if generic_dependencies:
            if dependencies:
                print(MAKEFILE_FROM_BUILD_DIR % dep_dir)
            pattern = '%'
            source = '$<'
            stem = '$*'
            python = f'$(_{dir}_python)'
            src_dir = f'$(_{dir}_dir)'
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
            embed = f"( if [ $(_{dir})_ != _ ]; then cd $(_{dir}) ; fi && %s"
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
        bringups = build_commands(parent_module.__doc__, 'Dependencies:', embed, end,
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

        result = doctest.testmod(parent_module)
        print(f"All {result.attempted} python usage examples PASS", )
        examples = build_commands(parser.epilog, "Examples:")
        run_command_examples(examples)
        print(f"All {len(examples)} command usage examples PASS")
        exit(0)


def add_arguments(argparser):
    argparser.add_argument('--makemake', action='store_true',
                           help=f"Print Makefile for {module_path}, and exit")
    argparser.add_argument('--generic', action='store_true',
                           help=f"Print generic Makefile for {module_path}, and exit")
    argparser.add_argument('--dep', action='store', help=(
        f"Build a {module}.dep target, print its Makefile include statement, and exit"))
    argparser.add_argument('--test', nargs=0, action=Test, help=(
        "Verify examples and exit"))


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
	python3 -c 'import sys; assert sys.version_info[:2] >= (3, 9), sys.version' > $@"""
               """ && \\
	python3 -m pip install pip >> $@

$ python3 makemake.py --dep makemake.dep --makemake
all: makemake.py.tested
	
makemake.py.tested: makemake.py makemake.dep makemake.py.bringup
	python3 makemake.py --test > $@
makemake.dep: makemake.py
	python3 makemake.py --dep $@
include makemake.dep
""")
    add_arguments(argparser)
    args = argparser.parse_args()
