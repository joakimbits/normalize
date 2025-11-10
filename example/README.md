### Doctests in [README.md](README.md):

\footnotesize
~~~ {.sh}
$ example
Hello from main.c!
Hello from greeter.cpp!

$ greeter.py
NAME
    greeter.py

SYNOPSIS
    greeter.py COMMAND

COMMANDS
    COMMAND is one of the following:

     hello
       Greetings from the source code examples in this folder

     run
       Run a command and return the decoded result

$ greeter.py hello
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

~~~
\normalsize

---

### How it works

- Makefile has 'bringup' as default target and includes make.mk (downloading it if missing).
- make.mk finds main.c and greeter.cpp, adds example[.exe], and includes build/main.c.d build/greeter.cpp.d.
- make.mk downloads make.py if missing, finds greeter.py, adds build/greeter.py.bringup, and includes build/greeter.py.mk.

\footnotesize
~~~ {.sh}
$ cat build/greeter.py.mk
$/build/greeter.py.bringup: $/greeter.py $/build/greeter.py.shebang $($/_EXE) | $/venv/$(VENV_PYTHON)  # Make sure $/greeter.py is setup OK
	$| -m pip install fire --no-warn-script-location > $@

$ greeter.py --help | awk '{ print "\t" $0 }'
	usage: greeter.py [-h] [--shebang] [--generic] [--make] [--dep DEP] [--pips]
	                  [-c C] [--timeout TIMEOUT] [--test] [--sh-test SH_TEST]
	
	Greetings from the source code
	
		function hello: Greetings from the source code examples in this folder
		function run: Run a command and return the decoded result
	
	option...:
	  -h, --help         show this help message and exit
	  --shebang          Insert a local venv shebang, print its PATH configuration
	                     if needed, and exit
	  --generic          Make generic build rules for all source code in the
	                     current directory in --make/--dep options
	  --make             Print Makefile for greeter.py, and exit
	  --dep DEP          Build a greeter.dep target, print its Makefile include
	                     statement, and exit
	  --pips             Print the path to pips within a python environment, and
	                     exit
	  -c C               Execute a program string and exit
	  --timeout TIMEOUT  Test timeout in seconds (3)
	  --test             Verify usage examples and exit
	  --sh-test SH_TEST  Test command usage examples in a file, and exit
	
	Examples:
	$ greeter.py
	NAME
	    greeter.py
	
	SYNOPSIS
	    greeter.py COMMAND
	
	COMMANDS
	    COMMAND is one of the following:
	
	     hello
	       Greetings from the source code examples in this folder
	
	     run
	       Run a command and return the decoded result
	
	$ greeter.py hello
	Hello from greeter.py!
	Hello from main.c!
	Hello from greeter.cpp!
	
	$ greeter.py run example
	Hello from main.c!
	Hello from greeter.cpp!
~~~
\normalsize
