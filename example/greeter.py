#!venv/Scripts/python.exe
"""Greetings from the source code

Dependencies:
fire
"""
import subprocess
import argparse

import make
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

    print("Hello from greeter.py!")
    print(run(f"{make.path}example"))

EXAMPLES = """
$ greeter.py
NAME
    greeter.py

SYNOPSIS
    greeter.py COMMAND

COMMANDS
    COMMAND is one of the following:

     hello
       Greetings from the source code examples in this folder

     run
       Run a command and return the decoded result

$ greeter.py hello
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

$ greeter.py run example
Hello from main.c!
Hello from greeter.cpp!
"""

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=make.brief(),
        epilog=f"Examples:{EXAMPLES}")
    make.add_arguments(argparser)
    args = argparser.parse_known_args()
    fire.Fire(dict(hello=hello, run=run))
