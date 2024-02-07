### Doctests in [README.md](README.md):

\footnotesize
~~~ {.sh}
$ ./example
Hello from main.c!
Hello from greeter.cpp!

$ ./greeter.py
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

$ ./greeter.py world
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
