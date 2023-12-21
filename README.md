# Bulk Audio Extract Tool

## About

## Install
Depending on your platform, to call python, you may need to use the command `python` or `python3`.
Typing `python3 --version` or `python --version` should display the currently installed python environment your PATH.
For the remainder of this document, replace instances of `python3` with the appropriate alias on your machine.

To install the requirements:
```bash
python3 -m pip install -r requirements.txt
```

Then, call `./main.py --help` to see application information.

## Add to Path

On Linux/MacOS, locate your `~/.bashrc` or `~/.zshrc` file and edit it, adding:
```bash
BAET_PATH="/path/to/BulkAudioExtractTool/main.py"
alias baet="python3 $(BAET_PATH)"
```
Restart your terminal and enter `baet --help`. The application's help screen should now show from any directory.