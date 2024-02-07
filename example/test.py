#!./venv/bin/python3
"""Greetings from the source code

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
    Hello from main.c!
    Hello from greeter.cpp!
    """
    print(f"Hello {world or 'from test.py'}!")
    if not world:
        print(run(f"{makemake.path}example"))

EXAMPLES = """
$ ./test.py
Hello from test.py!
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
