### Doctests in [README.md](README.md):

\footnotesize
~~~ {.sh}
$ ./example
Hello from main.c!
Hello from greeter.cpp!

$ ./greeter.py
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

$ ./greeter.py world
Hello world!

~~~
\normalsize

---

### How it works

- Makefile includes build.mk.
- build.mk includes test.py.mk.
- makemake builds both.

\footnotesize
~~~ {.sh}
$ cat build/greeter.py.mk
$/build/greeter.py.bringup: $/greeter.py $/build/greeter.py.mk | $/venv/bin/python3
	( cd $(dir $<). && make example --no-print-directory ) > $@ && \
	$(dir $<)venv/bin/python3 -m pip install fire --no-warn-script-location >> $@ && \
	$(dir $<)venv/bin/python3 $< --shebang >> $@

$ greeter.py --help | awk '{ print "\t" $0 }'
	usage: greeter.py [-h] [--makemake] [--generic] [--dep DEP] [-c C]
	                  [--timeout TIMEOUT] [--test] [--sh-test SH_TEST] [--shebang]
	                  ...
	
	Greetings from the source code
	
		function hello: Greetings from the source code examples in this folder
		function run: Run a command and return the decoded result
	
	positional arguments:
	  world              hello(world)
	
	option...:
	  -h, --help         show this help message and exit
	  --makemake         Print Makefile for greeter.py, and exit
	  --generic          Print generic Makefile for greeter.py, and exit
	  --dep DEP          Build a greeter.dep target, print its Makefile include
	                     statement, and exit
	  -c C               Execute a program string and exit
	  --timeout TIMEOUT  Test timeout in seconds (3)
	  --test             Verify usage examples and exit
	  --sh-test SH_TEST  Test command usage examples in a file, and exit
	  --shebang          Insert a local venv shebang, print its PATH configuration
	                     if needed, and exit
	
	Examples:
	$ ./greeter.py
	Hello from greeter.py!
	Hello from main.c!
	Hello from greeter.cpp!
	
	$ ./greeter.py world
	Hello world!

$ greeter.py README.md reader
Hello README.md reader!

~~~
\normalsize
