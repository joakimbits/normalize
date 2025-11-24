### Doctests in [README.md](README.md):

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

     run
       Run a command and return the decoded result

     hello
       Greetings from the source code examples in this folder

$ greeter.py hello
Hello from greeter.py!
Hello from main.c!
Hello from greeter.cpp!

~~~

---

### How it works

- Makefile has 'bringup' as default target and includes make.mk (downloading it if missing).
- make.mk finds main.c and greeter.cpp, adds example[.exe], and includes build/main.c.d build/greeter.cpp.d.
- make.mk downloads make.py if missing, finds greeter.py, adds build/greeter.py.bringup, and includes build/greeter.py.mk.

~~~ {.sh}
$ cat build/greeter.py.mk
$Bgreeter.py.bringup: $/greeter.py $Bgreeter.py.shebang $($/_EXE) | $($/_PYTHON)  # Make sure $/greeter.py is setup OK
	$| -m pip install fire --no-warn-script-location > $@
~~~
