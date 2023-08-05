#!./venv/bin/python3
"""Example usage of makemake

Before using or testing our module, install its dependencies via the Makefile:
    $ make
or, more specifically
    $ make build/test.py.bringup
or, by manually doing the pip install and linux commands listed under our Dependencies.

It is important that makemake is imported before any external dependencies for this
to work.

The generic ./Makefile here allows building from anywhere. It uses path prefix
variables to achieve that.

Here is how make does our bringup:

    It started with our Dependencies:
    $ make example --no-print-directory
    fire

    These dependencies were compiled by our main ./Makefile into two other Makefiles.
    $ python3 test.py --generic --dep build/test.py.d --makemake > build.mk

    The ./Makefile includes ./build.mk which in turn includes ./build/test.py.d.

    >>> print(run(f"cat {makemake.path}build.mk"))
    # ...
    _example_python = $(_example_dir)venv/bin/python
    _example_DEPS := $(_example_PY:$(_example)%=$(_example_build)%.d)
    ...
    # Include the autogenerated dependencies
    -include $(_example_DEPS)
    endif  # _example_dir

    >>> print(run(f"cat {makemake.path}build/test.py.d"))
    $(_example_build)test.py.bringup: $(_example)test.py $(_example_build)test.py.d
    $(_example_python)
    \t( cd $(_example_dir) && make example --no-print-directory ) > $@ && \\
    \t$(_example_python) -m pip install fire >> $@

    Here is that recipy output on first bringup:

    $ cat build/test.py.bringup
    g++ -S -nostartfiles -no-pie -I./ -MMD -MP  -c main.c -o build/main.c.s
    g++ -S -nostartfiles -no-pie -I./ -MMD -MP  -c greeter.cpp -o build/greeter.cpp.s
    cc -nostartfiles -no-pie  build/main.c.s build/greeter.cpp.s _start.s -o example
    Collecting fire
    ...
    Successfully installed fire-...

Our help text includes the command usage examples in our argparser epilog.

    >>> print(run(f"{makemake.path}venv/bin/python3 {makemake.path}test.py -h"))
    usage: test.py [-h] [--makemake] [--generic] [--dep DEP] [--test] [-c C] ...
    Example usage of makemake
    ...
    positional arguments:
      world       hello(world)
    ...
    Examples:
    $ ./test.py
    Hello from test.py!
    Hello from _start.s!
    Hello from main.c!
    Hello from greeter.cpp!
    $ ./test.py world
    Hello world!

A test report can be printed like this:

    $ make report
    ___ build/test.py.tested: ____
    All 5 python usage examples PASS
    All 2 command usage examples PASS
    ___ build/example.tested: ____
    Hello from _start.s!
    Hello from main.c!
    Hello from greeter.cpp!

Dependencies:
$ make example --no-print-directory
fire
"""
import subprocess
import argparse

import makemake
import fire

def run(cmd):
    """Run a command and return the decoded result

    >>> run('echo Hello world')
    'Hello world'
    """
    return subprocess.check_output(cmd.split()).decode('utf-8')[:-1]

def hello(world=None):
    """Greetings from the source code examples in this folder

    >>> hello()
    Hello from test.py!
    Hello from _start.s!
    Hello from main.c!
    Hello from greeter.cpp!
    """
    print(f"Hello {world or 'from test.py'}!")
    if not world:
        print(run(f"{makemake.path}example"))

EXAMPLES = """
$ ./test.py
Hello from test.py!
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

$ ./test.py world
Hello world!
"""

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
        epilog=f"Examples:{EXAMPLES}")
    argparser.add_argument('world', nargs=argparse.REMAINDER, help=(
        "hello(world)"))
    makemake.add_arguments(argparser)
    args = argparser.parse_args()
    fire.Fire(hello)
