# Tool for generating build dependencies: makemake.py
Any python module that imports makemake (and makemake itself) can print a Makefile for handling its dependencies and
tests. It can also print a generic Makefile for handling all source code in its directory, including .py, .c, cpp, .s.

Example: 
$ python3 makemake.py --makemake --generic > Makefile && make

This generic Makefile builds exactly the same targets also when included in a parent Makefile anywhere and isolates
its own dependencies into a local python venv.

The non-generic Makefile variant does not isolate its dependences. It can only be included from within the same folder.

Python version 3.7 or later is required.