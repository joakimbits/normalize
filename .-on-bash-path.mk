ifndef .-ON-PATH
PATHS := $(subst ;, ,$(subst :, ,$(PATH)))
ifeq (,$(filter .,$(PATHS)))
    .-ON-PATH := .-on-path
    .-on-path:
		# # Make local commands available without ./ prefix
		echo 'PATH=".:$$PATH"' >> ~/.bashrc
		# ToDo: source ~/.bashrc && make $(MAKECMDGOALS)
		false
else
    .-ON-PATH :=
endif
endif