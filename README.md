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

## Supported platforms

- **Linux (x86_64)**: the wheel is tagged with the glibc floor measured from
  the bundled binaries (currently `manylinux_2_35_x86_64` — glibc >= 2.35,
  the ubuntu-22.04 build floor). `linxiv-cli` needs only glibc. The `linxiv`
  GUI additionally requires system libraries that manylinux does not cover:
  GTK 3, WebKitGTK 4.1 (`libwebkit2gtk-4.1`), libsoup 3, and OpenSSL 3 —
  install them from your distro (Debian/Ubuntu: `libwebkit2gtk-4.1-0`,
  Fedora: `webkit2gtk4.1`).
- **macOS (arm64)**: built on GitHub's `macos-latest` runner; the wheel's
  platform tag reflects that runner's default deployment target. Intel Macs
  are not supported.
- **Windows (x86_64)**: standard MSVC build, no extra runtime requirements.

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
highest `GLIBC_*` symbol version the binaries require (what CI does):

```sh
objdump -T src/linxiv/bin/linxiv-* | grep -o 'GLIBC_[0-9.]*' | sort -Vu | tail -1
python -m wheel tags --platform-tag manylinux_2_35_x86_64 dist/linxiv-*-linux_x86_64.whl
```
