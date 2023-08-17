### Doctests in [README.md](README.md):

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

$ ./test.py world
Hello world!

~~~
\normalsize

---

### How it works

- Makefile includes build.mk.
- build.mk includes test.py.mk.
- makemake builds both.

\footnotesize
~~~ {.sh}
$ cat build/test.py.mk
$(_example_build)test.py.bringup: $(_example)test.py $(_example_build)test.py.mk $(_example_python)
	( cd $(_example_dir) && make example --no-print-directory ) > $@ && \
	$(_example_python) -m pip install fire >> $@ && \
	chmod +x $< >> $@

$ cat build.mk | grep -E '^_example |^_example_build |^_example_python '
_example := $(subst $(PWD)/,,$(_example_abspath))
_example_build := $(subst $(PWD)/,,$(_example_abspath)$(__example_build))
_example_python := $(_example_dir)venv/bin/python

~~~
\normalsize


---

### Standard and custom _start code

\footnotesize
~~~ {.sh}
$ rm _start.s example && make --no-print-directory && ./example
cc   build/main.c.s build/greeter.cpp.s -o example
Hello from main.c!
Hello from greeter.cpp!

$ git restore _start.s && make --no-print-directory && ./example
cc -nostartfiles -no-pie  _start.s build/main.c.s build/greeter.cpp.s -o example
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

~~~
\normalsize

