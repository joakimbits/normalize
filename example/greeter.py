#!venv/Scripts/python.exe
"""Greetings from the source code

Dependencies:
fire
"""
import subprocess

import make

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

if __name__ == '__main__':
    make.argparser.parse_known_args()
    import fire
    fire.Fire(dict([(name, item) for name, item in globals().items() if callable(item)]))
