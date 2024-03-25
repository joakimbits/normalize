#!venv/bin/python3
"""Programming example: Strings and numbers

>>> print(" ".join(fizz3fuzz5(*range(1, 101))))
1 2 Fizz 4 Buzz Fizz 7 8 Fizz Buzz 11 Fizz 13 14 FizzBuzz 16 17 Fizz 19 Buzz Fizz 22 23 Fizz Buzz 26 Fizz 28 29 FizzBuzz 31 32 Fizz 34 Buzz Fizz 37 38 Fizz Buzz 41 Fizz 43 44 FizzBuzz 46 47 Fizz 49 Buzz Fizz 52 53 Fizz Buzz 56 Fizz 58 59 FizzBuzz 61 62 Fizz 64 Buzz Fizz 67 68 Fizz Buzz 71 Fizz 73 74 FizzBuzz 76 77 Fizz 79 Buzz Fizz 82 83 Fizz Buzz 86 Fizz 88 89 FizzBuzz 91 92 Fizz 94 Buzz Fizz 97 98 Fizz Buzz

Dependencies:
fire
"""
import argparse

import build
import fire

def fizz3fuzz5(*numbers):
    """Yields Fizz and Fuzz or original dumber depending on if 3 and 5 factors exist in it"""

    for i in numbers:
        s = ""
        if i % 3 == 0:
            s += 'Fizz'
        if i % 5 == 0:
            s += 'Buzz'
        yield s or str(i)

EXAMPLES = """
$ ./factorize.py 1 3 5 15 100
1
Fizz
Buzz
FizzBuzz
Buzz
"""

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=build.brief(),
        epilog=f"Examples:{EXAMPLES}")
    build.add_arguments(argparser)
    argparser.add_argument('number', nargs=argparse.REMAINDER, help=fizz3fuzz5.__doc__)
    args = argparser.parse_args()
    fire.Fire(fizz3fuzz5)
