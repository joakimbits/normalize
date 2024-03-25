## Tool for using and reporting arbitrary nested projects 

---

```
$ GH="https://raw.githubusercontent.com"; curl $GH/joakimbits/normalize/main/template/Makefile -o Makefile && make
```

- Create executables from all source files.
- Recursively also in sub-directories with a README.md file, or any other .md file.

```
$ make pdf html slides
```

- Tests all usage examples, and generates project reports if they all PASS.

---

```
$ make old new review audit
```

- Analyze changes and use GPT to generate release notes.

---

Standalone variant:

```sh
$ build.py --makemake
bringup: build/build.py.bringup
tested: build/build.py.tested
build/build.py.tested: build.py build/build.py.shebang build/build.py.mk
	build.py --test > $@
build/build.py.shebang: build.py build/build.py.bringup
	$(PYTHON) build.py --shebang > $@
build/build.py.bringup: build.py | $(PYTHON)
	mkdir -p build/ && \
	$(PYTHON) -m pip install requests tiktoken --no-warn-script-location > $@

```

- Python version 3.8 or later is required.

[example/README.md](example/README.md)