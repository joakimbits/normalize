## Tool for using and reporting arbitrary nested projects 

---

Preparation - install ln, git and make:
- On MacOS:
```zsh
xcode-select --install
```

- On Ubuntu or Windows WSL: 
```bash
sudo apt update && sudo apt install -y git build-essential
```

- On Windows (admin PowerShell for setup below, then use bash.exe — Git Bash — not WSL's bash):
```powershell
reg add 'HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock' /v AllowDevelopmentWithoutDevLicense /t REG_DWORD /d 1 /f
iwr -useb get.scoop.sh | iex; & ~\scoop\shims\scoop.ps1 install git make
```

Then run this in your project directory:
```
curl https://raw.githubusercontent.com/joakimbits/normalize/main/Makefile -O && make
```

- Creates executables from all source files.
- Recursively also in sub-directories with a README.md file, or any other .md file.
- Once this small `Makefile` is committed, you can remove built (and other uncommited) files using `git clean -fxd`.

---

Test and document:

```
make pdf html slides
```

Analyze changes since your last release:

```
make old new review audit
```

---

User manual:

```sh
$ make.py -c 'print(__doc__)'
USER MANUAL

To integrate a tool.py module that uses make, check the Dependencies section in its
header. Dependencies can include pip installation lines as well as bash commands.

To install and self-test a tool.py that uses make:

    $ python3 tool.py --make > tool.mk && make -f tool.mk && tool.py --test

To install all such tools in a directory - while adding their dependencies into a directory python venv:

    $ python3 tool.py --make --generic > Makefile
    $ make
    <modify any source file in the same folder>
    $ make

The Makefile will automatically also compile any C/C++ code into assembly code for the CPU used,
and build an executable with that and any other assembly code it finds in the same folder.
It needs access to internet to grab a make.mk file that handles that, which in turn installs make.py.
If they are already in the directory or linked to from the directory, internet access is not needed.

Dependencies:
requests tiktoken # Needed for the --prompt option

```

- Python version 3.9 or later is required, and will be installed automatically if missing on the OS.

[example/README.md](example/README.md)