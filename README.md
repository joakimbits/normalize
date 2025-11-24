# Tool for using and reporting arbitrary nested projects

* Software and its documentation built and verified incrementally together as one unit.
* Keeps a technical file up-to-date for Continuous Integration, product release and CE.
* Gives immediate release recommendations using GPT_MODEL=gpt-3.5-turbo-16k GPT_TEMPERATURE=0.7 (configurable). 

---

## Preparation - install make

### MacOS

```zsh
xcode-select --install
```

### Ubuntu / WSL

```bash
sudo apt update && sudo apt install -y git build-essential
```

### Windows (PowerShell)

```powershell
iwr -useb get.scoop.sh | iex; & ~\scoop\shims\scoop.ps1 install git make python
git config --global core.symlinks true
setx MSYS "winsymlinks:nativestrict"
setx MAKEFLAGS "SHELL=$((Join-Path $HOME 'scoop\shims\bash.exe') -replace '\\','/') .SHELLFLAGS=-lc"
setx U "%USERPROFILE%\scoop\apps\git\current\usr\bin"
```

<details>
<summary>After Windows setup above, <strong>open a new terminal (click to see examples)</summary>

**Git Bash** (bash.exe) — *no prefix needed* (MSYS tools already on PATH)

**Other terminals** — Scoop installed tools are on PATH; *use U* for others

Example: Format an absolute path into mixed-mode (bash.exe vs cmd vs powershell)
```bash
$ cygpath -m C:/
C:/
```

```cmd
> %U%\cygpath.exe -m C:\
C:/
```

```PowerShell
PS > & "${env:U}\cygpath.exe" -m 'C:\'
C:/
```

</details>

---

## Build
From your project directory:
```bash
curl -O https://raw.githubusercontent.com/joakimbits/normalize/main/Makefile && make
```

- Builds executables from source files.
- Recurses into sub-directories containing a `README.md` (or any `.md`).
- After committing the small `Makefile`, clean untracked/built files:
  ```bash
  git clean -fxd
  ```

## Test & document
```bash
make pdf html slides
```

## Analyze changes since last release
```bash
make old new review audit
```

---

## User manual
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

> Python **3.9+** is required

See [`example/README.md`](example/README.md).
