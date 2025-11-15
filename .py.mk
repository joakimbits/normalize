# Python module bringup, tested using make.py

# Path/variable prefix
Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))

# Build directory
B ?= build/

# Modules to match
* ?= %

# Default python interpreter
PYTHON ?= $(shell command -v python3 || cygpath -m `which python.exe`)

# Python interpreter
$/_PYTHON ?= $(PYTHON)

# Matched Python modules here
$/*.py := $(filter-out $/make.py,$(wildcard $(subst %,*,$/$*.py)))

# Suggested targets
$/bringup: $($/*.py:$/%=$/$B%.bringup)  # Default: Make sure everything is setup OK
$/tested: $($/*.py:$/%=$/$B%.tested)  # Recommended: Make sure everything tested OK
$/self-test: $/.py/build/test.py.sh-test.tested

# Do not leave and risk using any broken stuff!
.DELETE_ON_ERROR:
.PRECIOUS: $($/*.py:$/%=$/$B%.shebang)

# Make sure a local build directory exists
ifneq (,$B)
  $/$B:
	  mkdir -p $@
endif

# Make sure the python module uses make, has the right python shebang and is on PATH
$/$B$*.py.shebang: $/make.py $/$*.py | $($/_PYTHON) $/$B
	$(firstword $|) $^ --shebang >> $@

# Make sure the python module has an up-to-date bringup recipy
$/$B$*.py.mk: $/$*.py $/$B$*.py.shebang | $(.-ON-PATH)
	$< --dep $@

# Include all those bringup recipies
-include $($/*.py:$/%=$/$B%.mk)

# Make sure the python module tested OK
$/$B$*.py.tested: $/$*.py $/$B$*.py.bringup
	$< --test > $@


### Document usage of this builder

# We are going build a python module with a doctest in a hello function available as a command line argument:
define SH-TEST
$$ cat build/test.py.tested
All 1 python usage examples PASS

$$ test.py

$$ test.py hello
Hello World!

$$ cat test.py

endef

# We are going verify all the command usages above:
define SH-TEST.EXPECTED
All 4 command usage examples PASS
endef

# After bringup, these are the exact sections we expect to see in the module:
define SHEBANG
#!...python...

endef
define DEPENDENCIES
"""
Dependencies:
pip
"""

endef
define IMPORTS
import make
import pip

endef
define FUNCTION
def hello():
    """
    >>> hello()
    Hello World!
    """
    print('Hello World!')

endef
define CLI
if __name__ == '__main__':
    make.argparser.parse_known_args()
    fire.fire(dict([(name, item) for name, item in globals().items() if callable(item)]))

endef

$/.py/build/:
	mkdir -p $(dir $@)

$/.py/build/test.py.sh-test.expected: | $/.py/build/
	$(file >$@,$(SH-TEST.EXPECTED))

$/.py/build/test.py.sh-test: | $/.py/build/
	$(file >$@,$(SH-TEST)$(SHEBANG)$(DEPENDENCIES)$(IMPORTS)$(FUNCTION)$(CLI))

$/.py/test.py: $/.py/build/test.py.sh-test | $/.py/build/
	$(file >$@,$(FUNCTION))

# Put the bare function into test.py and verify that make.py test.py --shebang inserts make into it:
$/.py/build/test.py.tested: $/.py/test.py $/.py.mk $/make.py | $/.py/
	@echo
	# Self-tested source code:
	cat $<
	@echo
	# The Makefile for .py source code:
	ln -sf ../.py.mk $|Makefile
	@echo
	# The python module that Makefile needs:
	ln -sf ../make.py $|make.py
	@echo
	# Now building $@
	(cd $| && make tested)

# Verify
$/.py/build/test.py.sh-test.tested: $/.py/build/test.py.sh-test \
  $/.py/build/test.py.tested $/.py/build/test.py.sh-test.expected | $/.py/
	@echo
	# Expected command line usage:
	cat $<
	@echo
	# Now verifying that
	(cd $| && test.py --sh-test $<) > $@ && \
	diff -u $(lastword $^) $@
