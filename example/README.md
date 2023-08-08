## Example usage of makemake

The Makefile here allows building from anywhere. It uses makemake to generate path prefix 
variables and generic rules to achieve that. 

Makemake builds and includes build.mk which in turn builds and includes build/*.mk. 

Its default target builds an executable and brings up a venv for the python module.

To build everything except the pdf report:
```
$ make tested
```

This is how prefixes are used in the Makefiles:

\footnotesize
~~~ {.sh}
$ cat build.mk | grep -E '^_example_build |^_example_python |^_example |^__|^_example_dir '
_example := $(subst $(PWD)/,,$(_example_abspath))
__example_build := build/
_example_build := $(subst $(PWD)/,,$(_example_abspath)$(__example_build))
_example_dir := ./$(_example)
_example_python := $(_example_dir)venv/bin/python

~~~

~~~ {.sh}
$ cat build/test.py.mk
$(_example_build)test.py.bringup: $(_example)test.py $(_example_build)test.py.mk $(_example_python)
	( cd $(_example_dir) && make example --no-print-directory ) > $@ && \
	$(_example_python) -m pip install fire >> $@

~~~
\normalsize

Usage examples:

\footnotesize
~~~ {.sh}
$ ./example
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

$ ./test.py
Hello from test.py!
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

~~~
\normalsize

Tests are reported like this:

\footnotesize
~~~ {.sh}
$ cat build/example.tested
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

$ cat build/test.py.tested
All 2 python usage examples PASS
All 2 command usage examples PASS

~~~
```
$ cat build/README.md.sh-test.tested
All 7 command usage examples PASS
```
\normalsize

The python help text includes the two command usage examples that were tested.

\footnotesize
~~~ {.sh}
$ ./test.py -h | sed 's/^/  /;s/optional arguments:/options:/'
  usage: test.py [-h] [--makemake] [--generic] [--dep DEP] [--timeout TIMEOUT]
                 [--test] [--sh-test SH_TEST] [-c C]
                 ...
  
  Greetings from the source code
  
  Dependencies:
  $ make example --no-print-directory
  fire
  
  positional arguments:
    world              hello(world)
  
  options:
    -h, --help         show this help message and exit
    --makemake         Print Makefile for ./test.py, and exit
    --generic          Print generic Makefile for ./test.py, and exit
    --dep DEP          Build a test.dep target, print its Makefile include
                       statement, and exit
    --timeout TIMEOUT  Test timeout in seconds (3)
    --test             Verify examples and exit
    --sh-test SH_TEST  Verify command examples in file and exit
    -c C               Program passed in as string
  
  Examples:
  $ ./test.py
  Hello from test.py!
  Hello from _start.s!
  Hello from main.c!
  Hello from greeter.cpp!
  
  $ ./test.py world
  Hello world!
~~~
\normalsize
