# linxiv (PyPI)

Thin Python wrapper that ships the prebuilt [linXiv](https://github.com/jakeuribe/linXiv)
Rust binaries inside a platform wheel and execs them. No Rust toolchain needed
to install or run.

```sh
pip install linxiv          # everything below
pip install "linxiv[app]"   # same, extras are opt-in markers only
pip install "linxiv[cli]"
```

| Command      | Bundled binary | What it is          |
| ------------ | -------------- | ------------------- |
| `linxiv`     | `linxiv-app`   | Tauri desktop app   |
| `linxiv-cli` | `linxiv-cli`   | Command-line client |

All arguments pass through to the Rust binary.

## Python API

`linxiv.Linxiv` mirrors the linXiv MCP/CLI surface; each method is one
`linxiv-cli` call returning parsed JSON. Errors raise `linxiv.LinxivError`.

```python
from linxiv import Linxiv

lx = Linxiv()                      # or Linxiv(data_dir="~/my-library")
results = lx.search_papers("quantum decoherence", max_results=5)
paper = lx.fetch_paper("2204.12985")           # saves + returns the record
proj = lx.create_project("thesis", tags=["qft"])
lx.add_paper_to_project(proj["id"], paper["source_id"])
lx.create_note(paper["source_id"], "Key result in §3", project_id=proj["id"])
```

Method groups: papers (search/fetch/list/get/repair/delete/restore),
tags, projects (incl. export/import, bibtex/obsidian), notes, annotations,
PDFs, trash, authors, DOI, settings, stats, backup/restore.
`Linxiv(data_dir=...)` sets `LINXIV_DATA_DIR`; default is the same library
the desktop app uses — avoid concurrent writes while the app is running.

## Building a wheel

Copy the release binaries for the target platform into `src/linxiv/bin/`,
then build — `setup.py` tags the wheel `py3-none-<platform>`:

```sh
cp ../linXiv/src-tauri/target/release/{linxiv-app,linxiv-cli} src/linxiv/bin/
pip wheel --no-deps -w dist .
```

For PyPI upload, retag the Linux wheel with a manylinux tag matching the
build machine's glibc, e.g.:

```sh
python -m wheel tags --platform-tag manylinux_2_34_x86_64 dist/linxiv-*-linux_x86_64.whl
```
