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

All arguments pass through to the Rust binary. The Python layer will
eventually mirror the Rust API; for now it only launches.

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
