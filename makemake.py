#!venv/bin/python3
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

To self-test all such tools in a directory - while adding their dependencies into a directory python venv:

    $ sudo apt update && sudo apt -y upgrade && sudo apt install -y make
    $ python3 tool.py --makemake --generic > Makefile
    $ make
    <modify any source file in the same folder>
    $ make

Dependencies:
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

GENERIC_MAKEFILE = f"""# {_}$ {" ".join(sys.argv)}
_Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst ./,,$(subst \,/,$(subst C:\,/c/,$(dir $(_Makefile)))))

ifneq (clean,$(findstring clean,$(MAKECMDGOALS)))
    $/project.mk: $/makemake.py
	    curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/Makefile -o $@
	$/makemake.py:
	    curl https://raw.githubusercontent.com/joakimbits/normalize/better_mac_support/makemake.py -o $@
endif

-include $/project.mk
"""
COMMENT_GROUP_PATTERN = re.compile(r"(\s*#.*)?$")


def make_rule(rule, commands, file=sys.stdout):
    """Make a Makefile build recipy"""
    print(rule, file=file)
    if commands:
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
            f"{output}\n"
            f"Received: {repr(received)}\n"
            f"{received}")


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
            build_dir, dep_filename = os.path.split(dep_file)
            dep_dir_now = build_dir
            if build_dir:
                prefix = _ + "/"
                build_dir = build_dir + "/"
                if build_dir.startswith(prefix):
                    build_dir = build_dir[len(prefix):]
        else:
            dep_dir_now = build_dir = 'build/'
            dep_filename = f'{module_py}.mk'
            dep_file = f'build/{module_py}.mk'

        if generic_dependencies:
            if dependencies:
                print(GENERIC_MAKEFILE)
            pattern = '%'
            source = '$<'
            stem = '$*'
            python = '$/venv/$(VENV_PYTHON)'
            recipy_python = '$(dir $<)venv/$(VENV_PYTHON)'
            src_dir = '$/'
            build_dir = '$/build/'
            build_dir_var_value = f"{src_dir}{build_dir}"
            generic = " --generic"
        else:
            pattern = module
            source = module_path
            stem = module
            python = '$(PYTHON)'
            recipy_python = python
            src_dir = ""
            build_dir = build_dir
            generic = ""

        if generic_dependencies:
            embed = "( cd $(dir $<). && %s"
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
                                  pip=f"{recipy_python} -m pip")
        bringups.append(([f'{recipy_python} {source} --shebang'], [''], []))
        bringups.append((['chmod +x $<'], [''], []))
        op = ">"
        remaining = len(bringups)
        for command_lines, comment_lines, output_lines in bringups:
            remaining -= 1
            glue = " &&" if remaining else ""
            commands += command_lines[:-1]
            commands.append(f'{command_lines[-1]} {op} $@{glue}')
            op = '>>'

        if generic_dependencies or dep_path:
            dep = f"{build_dir}{dep_filename} "
        else:
            dep = ""
            commands = [f"mkdir -p {build_dir}" + (" &&" if commands else "")] + commands

        bringup_rule = f"{build_dir}{module}.py.bringup: {src_dir}{module}.py {dep}| {python}"
        rules.append(
            (bringup_rule,
             commands))

        if not commands:
            commands += ["touch $@"]

        for rule, commands in rules:
            if rule == bringup_rule and (dep_path or generic_dependencies):
                if not generic_dependencies:
                    print(f"include {build_dir}{dep_filename}")

                if build_dir and not os.path.exists(dep_dir_now):
                    os.makedirs(dep_dir_now)

                if dep_path:
                    with open(dep_file, 'w+') as dep:
                        make_rule(rule, commands, file=dep)
            elif dependencies:
                make_rule(rule, commands)

        exit(0)


class Shebang(Action):
    """Insert a local venv shebang, print its PATH configuration if needed, and exit"""

    SHEBANG = '#!venv/bin/python3'

    def __call__(self, parser, args, values, option_string=None):
        shebang = None
        src = open(module_path).read()
        if src[:2] == '#!':
            shebang, src = src.split("\n", 1)

        if shebang != self.SHEBANG:
            open(module_path, 'wb').write(f'{self.SHEBANG}\n{src}'.encode())

        search_path = os.environ['PATH']
        search_dirs = search_path.split(os.pathsep)
        if '.' not in search_dirs:
            if os.pathsep == ';':
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
        ('Darwin', 'MacOSX'),
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

$ cat build/makemake.dep
build/makemake.py.bringup: makemake.py build/makemake.dep | $(PYTHON)
	$(PYTHON) -m pip install requests --no-warn-script-location > $@ && \\
	$(PYTHON) makemake.py --shebang >> $@ && \\
	chmod +x $< >> $@

$ makemake.py --dep build/makemake.dep --makemake
all: build/makemake.py.tested
build/makemake.py.tested: makemake.py build/makemake.dep build/makemake.py.bringup
	makemake.py --test > $@
build/makemake.dep: makemake.py
	makemake.py --dep $@
include build/makemake.dep
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
