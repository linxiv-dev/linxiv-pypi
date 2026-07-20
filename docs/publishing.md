# Publishing to PyPI

Publishing runs via `.github/workflows/python-publish.yml` using PyPI trusted
publishing (no API tokens). The GitHub deployment environment `pypi` already
exists on this repo.

## One-time PyPI setup (requires a human login)

The `linxiv` project does not exist on PyPI yet, so register a **pending**
trusted publisher at <https://pypi.org/manage/account/publishing/> with exactly:

| Field | Value |
|---|---|
| PyPI project name | `linxiv` |
| Owner | `linxiv-dev` |
| Repository name | `linxiv-pypi` |
| Workflow filename | `python-publish.yml` |
| Environment name | `pypi` |

The first successful publish creates the project and converts the pending
publisher into a regular one.

## Prerequisite

linXiv releases must contain the raw binary assets
(`linxiv-app-<triple>` / `linxiv-cli-<triple>`, `.exe` suffix on Windows) —
added by linxiv-dev/linXiv PR #164. The first publishable release is the one
cut after that PR merges.

## Release flow

1. Bump `version` in `pyproject.toml` to match the linXiv release
   (e.g. `0.2.0`). Commit.
2. Create a GitHub release on `linxiv-dev/linxiv-pypi` tagged `vX.Y.Z` — the
   same tag as the linXiv release whose binaries get bundled. The workflow
   enforces `version == tag` and downloads the `linxiv-{app,cli}-<triple>`
   assets from `linxiv-dev/linXiv` at that tag.

Alternatively, run the workflow manually (Actions → "Upload Python Package" →
Run workflow) with the linXiv tag as the `linxiv_tag` input.
