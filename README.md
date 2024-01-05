# Bulk Audio Extract Tool

<img src="./images/help-preview.svg" alt="baet help screen" style="display: block; margin: auto; max-height: 500px">

## About

Bulk Audio Extract Tool (BAET) is a commandline tool to bulk export audio tracks from within a single directory.

## Install

### Requirements

BAET will run on Windows, macOS, and Linux. Listed below the pre-installation requirements:

- FFmpeg ([website](https://ffmpeg.org))
- Python v3.11+ ([website](https://www.python.org))

### Installing BAET

Installation is done via `pip`.
Depending on your platform, to call python, you may need to use the command `python` or `python3`.
Typing `python3 --version` or `python --version` should display the currently installed python environment your PATH.
For the remainder of this document, replace instances of `python` with the appropriate alias on your machine.

To install the most recent stable release, use:

```bash
python -m pip install baet
```

For pre-releases, use:

```bash
python -m pip install baet --pre
```

To update/upgrade to a new version, use:

```bash
python -m pip install baet -U [--pre]
```

To verify your install, call

```bash
baet --version
```

## Usage

Once installed, calling `baet --help` will display the general help screen, showing a list of options you can use.

To simply extract the audio tracks of all videos in a directory `~/inputs`,
and extract each into a subdirectory of `~/outputs`, call

```bash
baet -i "~/inputs" -o "~/outputs"
```

Unless you add the option `--no-subdirs`, a video `~/inputs/my_video.mp4` will have each audio track individually
exported to an audio file located in `./outputs/my_video/`.

### Note on the help screen

Currently, the help screen contains descriptions starting with `[TODO]`.
This indicates that the associated option may or may not be implemented fully or at all.

## Known issues

- The option `--no-subdirs` may cause BAET to misbehave if two files are generated with the same name,
  unless the option `--overwrite` is given, in which case one file will be overwritten.
