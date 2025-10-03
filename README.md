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

User manual:

```sh
$  head -39 make.py
#!venv/bin/python3
"""Print a Makefile for handling a python module and exit

Adds the following command line options to the main module:

--make: Print a Makefile for bringup and test of the parent module.
--generic: Generalize it to make everything that is makeable within the parent module directory, and from anywhere.
--dep <file>: Create a separate Makefile for bringup of the parent module, and set the build directory to its parent
  directory.

Makes it easy to add the following command line options to the parent module:

--timeout: Time in seconds before giving up on a command-line test.
--sh-test <file>: Test command line usage examples in a file and exit.
--test: Verify python and command line usage examples in the module and exit.
-c <string>: Execute a program string in the module and exit.
--prompt <file> <openai model> <T> <rot13-encoded key>: Print a GPT continuation of the file and exit.


USER MANUAL

To integrate a tool.py module that uses make, check the Dependencies section in its
header. Dependencies can include pip installation lines as well as bash commands.

To self-test a tool.py that uses make - while adding its dependencies into python3:

    $ python3 tool.py --make > tool.mk && make -f tool.mk

To self-test all such tools in a directory - while adding their dependencies into a directory python venv:

    $ sudo apt update && sudo apt -y upgrade && sudo apt install -y make
    $ python3 tool.py --make --generic > Makefile
    $ make
    <modify any source file in the same folder>
    $ make

Dependencies:
requests tiktoken # Needed for the --prompt option
"""

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

---

Standalone variant with dynamic bringup:

```sh
$ make.py --make --dep make.py.mk
bringup: make.py.bringup
tested: make.py.tested
make.py.tested: make.py make.py.shebang make.py.mk
	make.py --test > $@
make.py.shebang: make.py make.py.bringup
	$(PYTHON) make.py --shebang > $@
make.py.mk: make.py | $(PYTHON)
	$(PYTHON) make.py --dep $@ > /dev/null
-include make.py.mk

```

- Python version 3.9 or later is required.

[example/README.md](example/README.md)