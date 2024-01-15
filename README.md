<img src="./images/logo.png" alt="Logo" style="display: block; max-width: 50%; margin: auto">

<h2 align="center">
    A commandline tool to bulk export audio tracks.
</h2>

<!-- TODO: https://shields.io/badges -->

<p align="center">
    <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/baet">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/baet">
    <img alt="PyPI - Implementation" src="https://img.shields.io/pypi/implementation/baet">
    <img alt="Python Version from PEP 621 TOML" src="https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FTimeTravelPenguin%2FBulkAudioExtractTool%2Fmain%2Fpyproject.toml">
</p>

<p align="center">
    <img alt="GitHub License" src="https://img.shields.io/github/license/TimeTravelPenguin/BulkAudioExtractTool">
    <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/TimeTravelPenguin/BulkAudioExtractTool/CI.yml">
    <img alt="GitHub last commit (by committer)" src="https://img.shields.io/github/last-commit/TimeTravelPenguin/BulkAudioExtractTool">
</p>

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

<img src="./docs/img/baet_help.svg" alt="baet help screen" style="display: block; margin: auto; max-height: 500px">

<img src="./docs/img/baet_extract_help.svg" alt="baet help screen" style="display: block; margin: auto; max-height: 500px">

<img src="./docs/img/baet_probe_help.svg" alt="baet help screen" style="display: block; margin: auto; max-height: 500px">

To simply extract the audio tracks of all videos in a directory `~/inputs`,
and extract each into a subdirectory of `~/outputs`, call

```bash
baet -i "~/inputs" -o "~/outputs"
```

Unless you add the option `--no-subdirs`, a video `~/inputs/my_video.mp4` will have each audio track individually
exported to an audio file located in `~/outputs/my_video/`.

### Note on the help screen

Currently, the help screen contains descriptions starting with `[TODO]`.
This indicates that the associated option may or may not be implemented fully or at all.

## Known issues

- The option `--no-subdirs` may cause BAET to misbehave if two files are generated with the same name,
  unless the option `--overwrite` is given, in which case one file will be overwritten.
