"""Thin launcher for linXiv: exec the Rust binary bundled in this wheel."""

import os
import subprocess
import sys

_BIN = os.path.join(os.path.dirname(__file__), "bin")


def _run(name):
    exe = os.path.join(_BIN, name + (".exe" if os.name == "nt" else ""))
    if not os.path.exists(exe):
        sys.exit(f"linxiv: missing bundled binary {exe} — wheel built without binaries?")
    argv = [exe] + sys.argv[1:]
    if os.name == "nt":  # execv on Windows detaches from the console
        sys.exit(subprocess.run(argv).returncode)
    os.execv(exe, argv)


def app():
    _run("linxiv-app")


def cli():
    _run("linxiv-cli")
