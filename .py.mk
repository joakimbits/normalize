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
$/self-test: $/.py/

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

# Self-test this builder
$/.py/: $/make.py
	mkdir -p $@ $@build/
	echo "print('Hello World!')" > $@test.py
	echo "~~~sh\n$ test.py\nHello World!\n~~~" > $@test.md
	ln -s ../.py.mk $@Makefile
	ln -s ../make.py $@make.py
	(cd $@ && make tested) && \
	rm -r $@
