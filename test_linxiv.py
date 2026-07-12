"""Wrapper-logic checks (mocks only, never runs the binaries): `python test_linxiv.py`."""

import json
import os
import sys
from unittest import mock

sys.path.insert(0, "src")
with mock.patch("linxiv.api._find_cli", return_value="/fake/linxiv-cli"):
    import linxiv


def _client(**responses):
    """Linxiv client whose subprocess.run is mocked; returns (client, run_mock)."""
    lx = linxiv.Linxiv(binary="/fake/linxiv-cli")
    run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="{}", stderr=""))
    return lx, run


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


def test_api_arg_assembly():
    lx, run = _client()
    with mock.patch("subprocess.run", run):
        lx.search_papers("qft", max_results=5)
        lx.create_project("thesis", tags=["qft", "cd"])
        lx.list_notes(project_id=3)
    calls = [c.args[0] for c in run.call_args_list]
    assert calls[0] == ["/fake/linxiv-cli", "search", "qft", "--source", "arxiv", "--max", "5"]
    assert calls[1] == ["/fake/linxiv-cli", "project", "create", "thesis", "--tags", "qft", "cd"]
    assert calls[2] == ["/fake/linxiv-cli", "note", "list", "--project-id", "3"]


def test_api_error_raises():
    lx, run = _client()
    # network commands print a diagnostic line before the {"error"} JSON line
    run.return_value = mock.Mock(
        returncode=1, stdout="",
        stderr='[search] arXiv request timed out\n{"error": "arXiv request timed out"}\n',
    )
    with mock.patch("subprocess.run", run):
        try:
            lx.get_paper("arxiv:0000.00000")
        except linxiv.LinxivError as e:
            assert str(e) == "arXiv request timed out"
        else:
            raise AssertionError("expected LinxivError")


def test_api_oserror_wrapped():
    lx = linxiv.Linxiv(binary="/nonexistent/linxiv-cli")
    try:
        lx.get_stats()
    except linxiv.LinxivError:
        pass
    else:
        raise AssertionError("expected LinxivError")


def test_fetch_nonarxiv_parses_stdout():
    lx, run = _client()
    run.return_value = mock.Mock(
        returncode=0, stdout=json.dumps({"source_id": "openalex:W31"}), stderr="",
    )
    with mock.patch("subprocess.run", run):
        paper = lx.fetch_paper("W31", source="openalex")
    assert paper == {"source_id": "openalex:W31"}
    assert run.call_count == 1  # must NOT re-read via `paper get` (assumes arxiv:)


def test_fetch_reads_back_json():
    # arxiv fetch prints Markdown; wrapper must not json-parse it, then re-reads the paper
    lx, run = _client()
    run.side_effect = [
        mock.Mock(returncode=0, stdout="# A Paper\nMarkdown...", stderr=""),
        mock.Mock(returncode=0, stdout=json.dumps({"source_id": "arxiv:2204.12985"}), stderr=""),
    ]
    with mock.patch("subprocess.run", run):
        paper = lx.fetch_paper("2204.12985")
    assert paper == {"source_id": "arxiv:2204.12985"}
    assert run.call_args_list[1].args[0][:3] == ["/fake/linxiv-cli", "paper", "get"]


def test_update_setting_encodes_json():
    lx, run = _client()
    with mock.patch("subprocess.run", run):
        lx.update_setting("pdf_dir", {"path": "/x"})
        lx.update_setting("theme", "dark")
    assert run.call_args_list[0].args[0][-1] == '{"path": "/x"}'
    assert run.call_args_list[1].args[0][-1] == "dark"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
