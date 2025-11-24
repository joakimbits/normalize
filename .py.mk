# Python module bringup, tested using make.py

# Path/variable prefix
Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))

# Build directory
B ?= build/

# Modules to match
* ?= %

# Default python interpreter
OSTYPE ?= $(shell echo $$OSTYPE)
ifneq (,$(findstring $(OSTYPE),win32 msys cygwin))
    PYTHON ?= $(shell cygpath -m `which python.exe`)
    VENV_PYTHON ?= Scripts/python.exe
else
    PYTHON ?= $(shell where python3)
    VENV_PYTHON ?= bin/python3
endif

# Python interpreter
$/_PYTHON ?= $/.venv/$(VENV_PYTHON)
$/_PIP_DIR ?= $($/_PYTHON:%/$(VENV_PYTHON)=%)/lib/site-packages/

# Matched Python modules here
$/*.py := $(wildcard $(subst %,*,$/$*.py))

# Suggested targets
$/bringup: $($/*.py:$/%=$/$B%.bringup)  # Default: Make sure everything is setup OK
$/tested: $($/*.py:$/%=$/$B%.tested)  # Recommended: Make sure everything tested OK
$/self-test: $/.py/build/test.py.sh-test.tested

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:
.PRECIOUS: $($/*.py:$/%=$/$B%.shebang)

# Make sure python exists where expected
$($/_PYTHON): | $(PYTHON)
	$| -m venv --upgrade-deps $(@:%/$(VENV_PYTHON)=%)

# Make sure a pip package exists
$($/_PIP_DIR)%: | $($/_PYTHON)
	 $| -m pip install --prefer-binary $*

# Make sure a local build directory exists
ifneq (,$B)
  $/$B:
	  mkdir -p $@
endif

# Make sure the python module uses make, has the right python shebang and is on PATH
$/$B$*.py.shebang: $/make.py $/$*.py | $($/_PYTHON) $/$B
	$(firstword $|) $^ --shebang >> $@

# Make sure . is on path by depending on $(.-ON-PATH)
-include $/.-on-bash-path.mk

# Make sure the python module has an up-to-date bringup recipy
$/$B$*.py.mk: $/$*.py $/$B$*.py.shebang | $(.-ON-PATH)
	$< --dep $@

# Include all those bringup recipies
-include $($/*.py:$/%=$/$B%.mk)

# Check Python 3.9 syntax
$B$*.py.syntax: $/$*.py | $($/_PYTHON) $($/_PIP_DIR)ruff
	$(firstword $|) -m ruff check --select=E9,F63,F7,F82 --target-version=py39 $< > $@ || (cat $@ && false)

# Check Python 3.9 style
$B$*.py.style: $/$*.py $B$*.py.syntax | $($/_PYTHON)
	$| -m ruff check --fix --target-version=py39 $< > $@ || (cat $@ && false)

# Make sure the python module tested OK
$/$B$*.py.tested: $/$*.py $/$B$*.py.style $/$B$*.py.bringup
	$< --test > $@


# self-test

define FUNCTION
def hello():
    """
    >>> hello()
    Hello World!
    """
    print('Hello World!')
endef

define SH-TEST
$$ cat build/test.py.tested
All 1 python usage examples PASS
All 0 command usage examples PASS

$$ test.py
NAME
    test.py

SYNOPSIS
    test.py COMMAND

COMMANDS
    COMMAND is one of the following:

     hello
       >>> hello() Hello World!

$$ test.py hello
Hello World!

endef

define SH-TEST.EXPECTED
All 3 command usage examples PASS
endef

$/.py/build/:
	mkdir -p $(dir $@)

$/.py/build/test.py.sh-test.expected: | $/.py/build/
	$(file >$@,$(SH-TEST.EXPECTED))

$/.py/build/test.py.sh-test: | $/.py/build/
	$(file >$@,$(SH-TEST))

$/.py/test.py: $/.py/build/test.py.sh-test | $/.py/build/
	$(file >$@,$(FUNCTION))

$/.py/build/test.py.tested: $/.py/test.py $/.py.mk $/make.py | $/.py/
	ln -sf ../.py.mk $|Makefile
	ln -sf ../make.py $|make.py
	(cd $| && make tested)

$/.py/build/test.py.sh-test.tested: $/.py/test.py $/.py/build/test.py.tested \
  $/.py/build/test.py.sh-test $/.py/build/test.py.sh-test.expected
	$< --sh-test $(word 3,$^) > $@ && \
	diff -u $(lastword $^) $@
