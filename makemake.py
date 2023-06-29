"""Print Makefile for handling bringup, test and clean of builds for the parent module, and exit

Usage:
    import makemake  # before importing (other) external dependencies

    if __name__ == '__main__':
        import argparse

        argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                            description=__doc__,
                                            epilog='''Command-line examples:
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
parent_dir = os.path.split(os.path.split(parent_module.__file__)[0])[1]
dir_var = f"{parent_dir}_dir"
build_dir_var = f"{parent_dir}_build_dir"
prog_py = sys.argv[0]
prog_dir, prog_filename = os.path.split(prog_py)
prog, ext = os.path.splitext(prog_filename)

MAKEFILE_HEADER_FROM_BUILD_DIR = f"""# {parent_dir}$ python3 {" ".join(sys.argv)}
# Generic builder inspired from C template on https://makefiletutorial.com/ Thanks to Job Vranish
# It automatically determines dependencies for you. 
# All you have to do is put your Python/C/C++ files in the {parent_dir} folder.
# Intermediate files are always built into {parent_dir}/build/, even if PWD is not {parent_dir}.
# That means this builder can be included in any other builder without risking mixup
# - as long as the {parent_dir}_* variables here are not used elsewhere.

.DELETE_ON_ERROR:

makefile_abspath := $(abspath $(lastword $(MAKEFILE_LIST)))
normalize_abspath := $(dir $(makefile_abspath))
{dir_var} := $(subst $(PWD)/,,$(normalize_abspath))
{build_dir_var} := $(subst $(PWD)/,,$(normalize_abspath)%s)

# We build .dep, .bringup and .test for .py almost like .d, .o and tests for .c/.cpp

.PHONY: all, test
"""

MAKEFILE_FOOTER = f"""
# Find all the C, C++ and ASM files we want to compile
# Note the single quotes around the * expressions. Make will incorrectly expand these otherwise.
{parent_dir}_SRCS := $(shell find $({dir_var}) -name '*.cpp' -or -name '*.c' -or -name '*.s')

# String substitution for every C/C++ file.
# As an example, {parent_dir}/hello.cpp turns into {parent_dir}/build/hello.cpp.o
{parent_dir}_OBJS := $({parent_dir}_OBJS:$({dir_var})%=$({build_dir_var})%.o)

# String substitution (suffix version without %).
# As an example, build/hello.cpp.o turns into build/hello.cpp.d
{parent_dir}_DEPS := $({parent_dir}_OBJS:.o=.d)

# Every source folder in {parent_dir} will need to be passed to GCC so that it can find header files
{parent_dir}_INC_DIRS := $(shell find $({dir_var}) -type d)
# Add a prefix to {parent_dir}_INC_DIRS. So moduleA would become -ImoduleA. GCC understands this -I flag
{parent_dir}_INC_FLAGS := $(addprefix -I,$({parent_dir}_INC_DIRS))

# The -MMD and -MP flags together generate Makefiles for us!
# These files will have .d instead of .o as the output.
{parent_dir}_CPPFLAGS := $({parent_dir}_INC_FLAGS) -MMD -MP

# The final build step.
$({build_dir_var}){parent_dir}: $({parent_dir}_OBJS)
	$(CXX) $({parent_dir}_OBJS) -o $@ $(LDFLAGS)

# Build step for C source
$({build_dir_var})%.c.o: $({dir_var})%.c
	mkdir -p $(dir $@)
	$(CC) $({parent_dir}_CPPFLAGS) $(CFLAGS) -c $< -o $@

# Build step for C++ source
$({build_dir_var})%.cpp.o: $({dir_var})%.cpp
	mkdir -p $(dir $@)
	$(CXX) $({parent_dir}_CPPFLAGS) $(CXXFLAGS) -c $< -o $@

.PHONY: clean, clean_{parent_dir}
clean: clean_{parent_dir}
clean_{parent_dir}:
	rm -r $({build_dir_var})

# Include the .d makefiles. The - at the front suppresses the errors of missing
# Makefiles. Initially, all the .d files will be missing, and we don't want those
# errors to show up.
-include $({parent_dir}_DEPS)
"""
COMMENT_GROUP_PATTERN = re.compile("(\s*#.*)?$")


def make_rule(rule, commands, file=sys.stdout):
    print(rule, file=file)
    print('\t' + " \\\n\t".join(commands), file=file)


def build_commands(doc, heading, embed="%s", end="", pip=False):
    before_after = re.split(f'{heading}\s*((?:\S.*\r?\n)*)', doc, maxsplit=1)
    commands = []
    if len(before_after) >= 2:
        for line in before_after[1].split('\n'):
            command_lines, comment_lines, output_lines = commands[-1] if commands else ([], [], [])
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
                commands.append((["pip3 install " + command], [comment], []))

    return commands


def run_command_examples(commands):
    import subprocess

    for i, (command_lines, comment_lines, output_lines) in enumerate(commands):
        command = "\n".join(command_lines)
        if prog_dir:
            command = f"( cd {prog_dir} && {command} )"
        output = "\n".join(output_lines)
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=3)
        assert not result.returncode, f"Example {i + 1} failed during execution of $ {command}"
        received = result.stdout or ""
        assert received == output, f"Example {i + 1}: $ {command}\nExpected: {repr(output)}\nReceived: {repr(received)}"


if parent_module.__name__ == '__main__':
    dependencies = '--makemake' in sys.argv[1:]
    generic_dependencies = '--makemake_generic' in sys.argv[1:]
    separate_bringup = '--makemake_dep' in sys.argv[1:]
    gcc_builder = '--makemake_gcc' in sys.argv[1:]
    if dependencies or generic_dependencies or separate_bringup:
        assert len(sys.argv) == sum([1, dependencies, generic_dependencies, separate_bringup * 2, gcc_builder]), (
            sys.argv, [1, dependencies, generic_dependencies, separate_bringup * 2, gcc_builder])

        if separate_bringup:
            dep_file = sys.argv[sys.argv.index('--makemake_dep', 1) + 1]
            assert dep_file[:2] != "__", sys.argv
            dep_dir, dep_filename = os.path.split(dep_file)
            dep_dir_now = dep_dir
            if dep_dir:
                dep_dir = (dep_dir + "/").removeprefix(parent_dir + "/")
        else:
            dep_dir = "build/"
            dep_filename = prog + ".dep"
            dep_file = f"build/{prog}.dep"

        if generic_dependencies:
            if dependencies:
                print(MAKEFILE_HEADER_FROM_BUILD_DIR % dep_dir)
            pattern = '%'
            source = '$<'
            stem = '$*'
            src_dir = f"$({dir_var})"
            build_dir = f"$({build_dir_var})"
            build_dir_var_value = f"{src_dir}{dep_dir}"
            dep_pattern = f"{build_dir}{dep_filename.replace(prog, pattern)}"
            generic = " --makemake_generic"
        else:
            pattern = prog
            source = prog_py
            stem = prog
            src_dir = ""
            build_dir = dep_dir
            dep_pattern = dep_file
            generic = ""

        bringup_rule = f"{build_dir}{prog}.bringup: {src_dir}{prog}.py {build_dir}{dep_filename}"

        commands = []
        rules = [
            (f"all: test", []),
            (f"test: {build_dir}{prog}.tested", []),
            (f"{build_dir}{pattern}.tested: {src_dir}{pattern}.py {dep_pattern} {build_dir}{pattern}.bringup",
             [f"python3 {source} --test > $@"]),
            (bringup_rule,
             commands),
            (f"{dep_pattern}: {src_dir}{pattern}.py",
             [f"python3 {source} --makemake_dep $@{generic}"]),
        ]

        if not gcc_builder:
            rules += [(f"clean_{src_dir}{pattern}:",
                       [f"rm {dep_pattern.replace(pattern, stem)} {build_dir}{stem}.bringup {build_dir}{stem}.tested"]),
                      (f"clean: clean_{src_dir}{prog}", []),]

        if generic_dependencies:
            embed, end = f"( if [ $({dir_var})_ != _ ]; then cd $({dir_var}) ; fi && %s", " )"
        else:
            embed, end = "%s", ""

        bringups = build_commands(parent_module.__doc__, "Dependencies:", embed, end, pip=True)
        if bringups:
            op = ">"
            remaining = len(bringups)
            for command_lines, comment_lines, output_lines in bringups:
                remaining -= 1
                glue = " &&" if remaining else ""
                commands += command_lines[:-1]
                commands.append(f'{command_lines[-1]} {op} $@{glue}')
                op = ">>"

        if not commands:
            commands += ["touch $@"]

        for rule, commands in rules:
            if separate_bringup and rule == bringup_rule:
                print(f"include {build_dir}{dep_filename}")
                if dep_dir and not os.path.exists(dep_dir_now):
                    os.makedirs(dep_dir_now)
                with open(dep_file, 'w+') as dep:
                    make_rule(rule, commands, file=dep)
            elif dependencies:
                make_rule(rule, commands)

        if gcc_builder:
            print(MAKEFILE_FOOTER)

        exit(0)


class Test(Action):
    """
    Doctest python examples in parent_module, test command usage examples in this argparser epilog, and exit
    """
    def __call__(self, parser, args, values, option_string=None):
        import doctest

        doctest.testmod(parent_module)
        run_command_examples(build_commands(parser.epilog, "Examples:"))
        exit(0)


def add_arguments(argparser):
    argparser.add_argument('--makemake', action='store_true',
                           help=f"Print Makefile for {prog_py}, and exit")
    argparser.add_argument('--makemake_generic', action='store_true',
                           help=f"Print generic Makefile for {prog_py}, and exit")
    argparser.add_argument('--makemake_dep', action='store',
                           help=f"Build a {prog}.dep target, print its Makefile include statement, and exit")
    argparser.add_argument('--makemake_gcc', action='store_true',
                           help=f"Print a generic gcc builder for C/C++/ASM source in {parent_dir}, and exit")
    argparser.add_argument('--test', nargs=0, action=Test, help="Verify examples and exit")


if __name__ == '__main__':
    import argparse

    argparser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                        description=__doc__,
                                        epilog="""Examples:
$ python3 makemake.py --makemake_dep makemake.dep
include makemake.dep

$ cat makemake.dep
makemake.bringup: makemake.py makemake.dep
	python3 -c 'import sys; assert sys.version_info[:2] >= (3, 9), sys.version' > $@ && \\
	pip3 install pip >> $@

$ python3 makemake.py --makemake_dep makemake.dep --makemake
all: test
	
test: makemake.tested
	
makemake.tested: makemake.py makemake.dep makemake.bringup
	python3 makemake.py --test > $@
include makemake.dep
makemake.dep: makemake.py
	python3 makemake.py --makemake_dep $@
clean_makemake:
	rm makemake.dep makemake.bringup makemake.tested
clean: clean_makemake
	
""")
    add_arguments(argparser)
    args = argparser.parse_args()
