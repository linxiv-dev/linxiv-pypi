"""Launcher-logic check (mocks only, never runs the binaries): `python test_linxiv.py`."""

import os
import sys
from unittest import mock

sys.path.insert(0, "src")
import linxiv


def test_execs_bundled_binary():
    with mock.patch("os.path.exists", return_value=True), \
         mock.patch("os.execv") as execv, \
         mock.patch.object(sys, "argv", ["linxiv-cli", "search", "qft"]):
        linxiv.cli()
    exe = os.path.join(linxiv._BIN, "linxiv-cli")
    execv.assert_called_once_with(exe, [exe, "search", "qft"])


def test_exits_when_binary_missing():
    with mock.patch("os.path.exists", return_value=False):
        try:
            linxiv.app()
        except SystemExit as e:
            assert "linxiv-app" in str(e.code)
        else:
            raise AssertionError("expected SystemExit")


if __name__ == "__main__":
    test_execs_bundled_binary()
    test_exits_when_binary_missing()
    print("ok")
