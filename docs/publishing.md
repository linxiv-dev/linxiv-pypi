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

> **Do not move the publish job out of `python-publish.yml`.** PyPI validates
> the OIDC `job_workflow_ref` claim against the workflow filename above, and it
> does not support reusable workflows — a job that publishes from a
> `workflow_call` file fails with `invalid-publisher`. Other workflows must
> *dispatch* `python-publish.yml`, not absorb its publish job.

## Prerequisite

linXiv releases must contain the raw binary assets
(`linxiv-app-<triple>` / `linxiv-cli-<triple>`, `.exe` suffix on Windows).
`sync-linxiv.yml` verifies all six are present before opening a bump PR, so an
incomplete upstream release fails early rather than midway through the wheel
matrix.

## Release flow (automated)

Releases follow linXiv automatically, gated on one human merge:

1. **`sync-linxiv.yml`** polls `linxiv-dev/linXiv` daily (and on manual dispatch,
   or a `linxiv-released` `repository_dispatch`). When `/releases/latest` — which
   excludes drafts and prereleases — reports a newer tag than `pyproject.toml`,
   it verifies the six binaries exist, bumps `version`, and opens a PR.
2. **You review and merge that PR.** This is the ship gate. PyPI versions cannot
   be reused, so close the PR instead of merging if anything looks wrong.
3. **`release-on-merge.yml`** fires on a `pyproject.toml` change landing on
   `main`. If `vX.Y.Z` isn't already released, it tags the merge commit, creates
   the GitHub release, and dispatches `python-publish.yml` with `linxiv_tag`.
4. **`python-publish.yml`** builds the three platform wheels, runs
   `test_linxiv.py` against each, and uploads to PyPI.

Step 3 dispatches rather than relying on the `release: published` trigger
because releases created with the default `GITHUB_TOKEN` do not start other
workflow runs; `workflow_dispatch` is an explicit exception to that rule. This
also guarantees exactly one publish run per release rather than two.

### Making it instant instead of daily

Add a step to linXiv's release workflow — after the binary assets finish
uploading — that POSTs a `repository_dispatch` to this repo:

```yaml
- env:
    GH_TOKEN: ${{ secrets.PYPI_REPO_DISPATCH_TOKEN }} # PAT/App token, write access to linxiv-pypi
  run: |
    gh api repos/linxiv-dev/linxiv-pypi/dispatches \
      -f event_type=linxiv-released
```

Nothing in this repo changes; `sync-linxiv.yml` already listens for it.

## Upgrading for stable releases + prerelease channels

Today this package tracks linXiv's stable line only: `/releases/latest` excludes
drafts and prereleases, so an upstream `v0.5.0-rc.1` is ignored entirely. That is
the right behaviour while linXiv is alpha and every release is the release.

Once linXiv starts cutting stable releases with rc/beta tags alongside them and
you want testers on `pip install --pre linxiv`, four changes have to land
together — there's a full breakdown in the `UPGRADE` comment at the top of
`sync-linxiv.yml`'s "Resolve latest upstream release" step. Summary:

1. Query `/releases` (includes prereleases) instead of `/releases/latest`.
2. Normalize tags to PEP 440 — `v0.5.0-rc.1` → `0.5.0rc1`. This breaks the
   `version == tag` invariant `python-publish.yml` enforces.
3. Replace the `sort -V` forward-check with `packaging.version.Version`.
4. Bump the `Development Status` classifier in `pyproject.toml`.

Step 3 is the one that bites silently. GNU version sort ranks `0.4.0rc1` *above*
`0.4.0`, while PEP 440 ranks it below — so publishing `0.4.0` final after
`0.4.0rc1` would look like a version regression and hard-fail the sync. Steps 1
and 4 are inert until you make them, and step 2 fails loudly.

## Manual release

Either path still works:

- Bump `version` in `pyproject.toml`, commit to `main`, and let
  `release-on-merge.yml` do the rest.
- Or cut a GitHub release tagged `vX.Y.Z` by hand — `python-publish.yml` keeps
  its `release: published` trigger. It enforces `version == tag`.
- Or run it directly (Actions → "Upload Python Package" → Run workflow) with
  the linXiv tag as the `linxiv_tag` input.
