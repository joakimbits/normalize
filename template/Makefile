# Prefixing project variable names with $/_ and project files with $/ to make this Makefile usable from anywhere
Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))
$/bringup:

# Bringup executables and define 'tested report html pdf slides audit' targets for .md .py .cpp .c .s sources here.
$/build/project.mk:
	mkdir -p $(dir $@) && curl https://raw.githubusercontent.com/joakimbits/normalize/main/Makefile -o $@
-include $/build/project.mk