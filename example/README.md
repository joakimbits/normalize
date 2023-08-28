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
$(_example_BUILD)test.py.bringup: $(_example)test.py $(_example_BUILD)test.py.mk $(_example_PYTHON)
	( cd $(_example_DIR) && make example --no-print-directory ) > $@ && \
	$(_example_PYTHON) -m pip install fire >> $@ && \
	chmod +x $< >> $@

$ cat build.mk | grep -E '^_example |^_example_BUILD |^_example_PYTHON '
_example := $(subst $(PWD)/,,$(_example_ABSPATH))
_example_BUILD := $(subst $(PWD)/,,$(_example_ABSPATH)$(__example_BUILD))
_example_PYTHON := $(_example_DIR)venv/bin/python

~~~
\normalsize


---

### Standard and custom _start code

\footnotesize
~~~ {.sh}
$ mv example _start.s build/ && make --no-print-directory && ./example
cc  build/main.c.s build/greeter.cpp.s -o example
Hello from main.c!
Hello from greeter.cpp!

$ rm example && mv build/_start.s . && make --no-print-directory && ./example
cc -nostartfiles -no-pie _start.s build/main.c.s build/greeter.cpp.s -o example
Hello from _start.s!
Hello from main.c!
Hello from greeter.cpp!

$ mv build/example .
~~~
\normalsize

