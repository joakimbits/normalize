## Tool for generating build dependencies: makemake.py
Any python module that imports makemake (and makemake itself) can print a Makefile for handling its dependencies and
tests. It can also print a generic Makefile for handling all source code in its directory, including .py, .c, cpp, .s.

Compile local sources and bringup a local venv ready to run all local python modules.
```
$ python3 makemake.py --makemake --generic > Makefile && make
```

Test the python and command line usage examples, and generate a project report.
```
$ make pdf
```

The generic Makefile builds exactly the same targets also when included in a parent Makefile anywhere. It also isolates
its own dependencies into a local python venv.

The non-generic Makefile variant does not isolate its dependencies. It can only be included from within the same folder.

Python version 3.7 or later is required.

[example/README.md](example/README.md)

[example/report.html](example/report.html)