#!venv/bin/python
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

def hello(*world):
    """Greetings from the source code examples in this folder

    >>> hello()
    Hello from greeter.py!
    Hello from main.c!
    Hello from greeter.cpp!
    """

    if world:
        print(f"Hello {' '.join(world)}!")
    else:
        print("Hello from greeter.py!")
        print(run(f"{makemake.path}example"))

EXAMPLES = """
$ ./greeter.py
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

$ ./greeter.py world
Hello world!
"""

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=makemake.brief(),
        epilog=f"Examples:{EXAMPLES}")
    argparser.add_argument('world', nargs=argparse.REMAINDER, help=(
        "hello(world)"))
    makemake.add_arguments(argparser)
    args = argparser.parse_args()
    fire.Fire(hello)
