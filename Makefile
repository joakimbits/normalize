# Prefixing project variable names with $/_ and project files with $/ to make this Makefile usable from anywhere
Makefile := $(lastword $(MAKEFILE_LIST))
/ := $(patsubst %build/,%,$(patsubst ./%,%,$(patsubst C:/%,/c/%,$(subst \,/,$(dir $(Makefile))))))
$/bringup:

# Bringup executables and define 'tested report html pdf slides audit' targets for .md .py .cpp .c .s sources here.
$/make.mk:
	if [ -e "$(dir $@)../make.mk" ]; then \
	  ln -sf ../make.mk "$@"; \
	else \
	  curl https://raw.githubusercontent.com/joakimbits/normalize/main/make.mk -o $@; \
	fi

-include $/make.mk