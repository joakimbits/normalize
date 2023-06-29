# normalize$ python3 makemake.py --makemake_generic --makemake_dep build/makemake.dep --makemake --makemake_gcc
# Generic builder inspired from C template on https://makefiletutorial.com/ Thanks to Job Vranish
# It automatically determines dependencies for you. 
# All you have to do is put your Python/C/C++/ASM files in the normalize folder.
# Intermediate files are always built into normalize/build/, even if PWD is not normalize.
# That means this builder can be included in any other builder without risking mixup
# - as long as the normalize_* variables here are not used elsewhere.

# Make sure failed build results are automatically deleted.
.DELETE_ON_ERROR:

makefile_abspath := $(abspath $(lastword $(MAKEFILE_LIST)))
normalize_abspath := $(dir $(makefile_abspath))
normalize_dir := $(subst $(PWD)/,,$(normalize_abspath))
normalize_build_dir := $(subst $(PWD)/,,$(normalize_abspath)build/)

ifeq ($(normalize_dir),)
normalize_dir_or_pwd := .
_normalize_or_nothing :=
else
normalize_dir_or_pwd := $(normalize_dir)
_normalize_or_nothing := _$(normalize_dir:%/=%)
endif

# Find all the Python files
normalize_PY := $(wildcard $(normalize_dir)*.py)

# List the make, test and tested targets for Python files

# Since each Python module here import makemake, it can manage its own bringup.
# As an example, normalize/build/hello.dep will contain a single normalize/build/hello.bringup target.
# That target recipy has bash commands for bringup of all external pip modules and bash commands listed under
# the title "Dependencies:" at the end of the header of normalize/hello.py. Lines that begin with "$ " are
# interpreted as bash commands. Other lines interpreted as pip module specifications.
# All bash and pip commands are chained in exactly the order listed under "Dependencies:" and their output teed into
# normalize/build/hello.bringup.
#
# ToDo: Make makemake do the actual --bringup instead of generating a Make target recipy for it like this.
# ToDo: Do all the pip and apt bringup in a module-unique virtualenv.
# (Now we risk failing or building with wrong dependencies is there are conflicts between modules.)
$(normalize_build_dir)%.dep: $(normalize_dir)%.py
	python3 $< --makemake_generic --makemake_dep $@
normalize_DEPS := $(normalize_PY:$(normalize_dir)%.py=$(normalize_build_dir)%.dep)
normalize_BRINGUPS := $(normalize_PY:$(normalize_dir)%.py=$(normalize_build_dir)%.bringup)
normalize_TESTEDS := $(normalize_PY:$(normalize_dir)%.py=$(normalize_build_dir)%.tested)

.PHONY: all
all: $(normalize_TESTEDS)
$(normalize_build_dir)%.tested: $(normalize_dir)%.py $(normalize_build_dir)%.dep $(normalize_build_dir)%.bringup
	python3 $< --test > $@

# Find all the C, C++ and ASM files
normalize_SRC := $(shell find $(normalize_dir_or_pwd) -name '*.cpp' -or -name '*.c' -or -name '*.s')

# String substitution for every C/C++ file.
# As an example, normalize/hello.cpp turns into normalize/build/hello.cpp.o
normalize_OBJS := $(normalize_SRCS:$(normalize_dir)%.c=$(normalize_build_dir)%.c.o)
normalize_OBJS += $(normalize_SRCS:$(normalize_dir)%.cpp=$(normalize_build_dir)%.cpp.o)

# String substitution for every object file (suffix version without %).
# As an example, build/hello.cpp.o turns into build/hello.cpp.d
normalize_DEPS += $(normalize_OBJS:.o=.d)

# Every source folder in normalize will need to be passed to GCC so that it can find header files
normalize_INC_DIRS := $(shell find $(normalize_dir) -type d)
# Add a prefix to normalize_INC_DIRS. So moduleA would become -ImoduleA. GCC understands this -I flag
normalize_INC_FLAGS := $(addprefix -I,$(normalize_INC_DIRS))

# The -MMD and -MP flags together generate Makefiles for us!
# These files will have .d instead of .o as the output.
normalize_CPPFLAGS := $(normalize_INC_FLAGS) -MMD -MP

# The final build step.
$(normalize_build_dir)normalize: $(normalize_OBJS)
	$(CXX) $(normalize_OBJS) -o $@ $(LDFLAGS)

# Build step for C source
$(normalize_build_dir)%.c.o: $(normalize_dir)%.c
	mkdir -p $(dir $@)
	$(CC) $(normalize_CPPFLAGS) $(CFLAGS) -c $< -o $@

# Build step for C++ source
$(normalize_build_dir)%.cpp.o: $(normalize_dir)%.cpp
	mkdir -p $(dir $@)
	$(CXX) $(normalize_CPPFLAGS) $(CXXFLAGS) -c $< -o $@

# Include the makefiles now built.
-include $(normalize_DEPS)

# Cleanup is simple - just remove the build folder.
.PHONY: clean$(_normalize_or_nothing)
clean$(_normalize_or_nothing):
	rm -r $(normalize_build_dir)



