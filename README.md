## Tool for using and reporting arbitrary nested projects 

---

Run this in your project directory:

```
curl https://raw.githubusercontent.com/joakimbits/normalize/main/Makefile -O && make
```

- Creates executables from all source files.
- Recursively also in sub-directories with a README.md file, or any other .md file.

---

Test and document:

```
make pdf html slides
```

Analyze changes since your last release:

```
make old new review audit
```

---

Standalone variant:

```sh
$ make.py --make
bringup: build/make.py.bringup
tested: build/make.py.tested
build/make.py.tested: make.py build/make.py.shebang
	make.py --test > $@
build/make.py.shebang: make.py build/make.py.bringup
	$(PYTHON) make.py --shebang > $@
build/make.py.bringup: make.py | $(PYTHON)
	mkdir -p build/ && \
	$(PYTHON) -m pip install requests tiktoken --no-warn-script-location > $@

```

Standalone variant with dynamic bringup:

```sh
$ make.py --make --dep build/make.py.mk
bringup: build/make.py.bringup
tested: build/make.py.tested
build/make.py.tested: make.py build/make.py.shebang build/make.py.mk
	make.py --test > $@
build/make.py.shebang: make.py build/make.py.bringup
	$(PYTHON) make.py --shebang > $@
build/make.py.mk: make.py | $(PYTHON)
	$(PYTHON) make.py --dep $@ > /dev/null
-include build/make.py.mk

```

- Python version 3.9 or later is required.

[example/README.md](example/README.md)