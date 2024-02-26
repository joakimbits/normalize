## Tool for generating build dependencies: makemake.py

---

```
$ python3 makemake.py --makemake --generic > Makefile && make
```

- Compiles local sources and installs a local venv ready to run all local python modules.

```
$ make pdf html slides
```

- Tests the python and command line usage examples, and generates project reports.

---

- The generic Makefile builds exactly the same when included in a parent Makefile anywhere. 
- It also isolates its own dependencies into a local python venv. 

There is a simpler variant:

- It can only be included from within the same directory, without a venv.

---

```sh
$ python3 makemake.py --makemake
all: build/makemake.py.tested
build/makemake.py.tested: makemake.py build/makemake.py.bringup
	makemake.py --test > $@
build/makemake.py.bringup: makemake.py | $(PYTHON)
	mkdir -p build/ && \
	$(PYTHON) -m pip install requests --no-warn-script-location > $@ && \
	$(PYTHON) makemake.py --shebang >> $@ && \
	chmod +x $< >> $@

```

- Python version 3.7 or later is required.

[example/README.md](example/README.md)