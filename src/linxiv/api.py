"""Programmatic linXiv API: thin JSON wrapper over the bundled linxiv-cli binary.

Method names mirror the linXiv Python/MCP surface (search_papers, create_project,
...); every call is one CLI subprocess that prints JSON on stdout and
{"error": msg} on stderr with exit 1.
"""

import json
import os
import shutil
import subprocess

_BIN = os.path.join(os.path.dirname(__file__), "bin")


class LinxivError(RuntimeError):
    """linxiv-cli exited non-zero; str(exc) is the CLI's error message."""


def _find_cli():
    exe = os.path.join(_BIN, "linxiv-cli" + (".exe" if os.name == "nt" else ""))
    if os.path.exists(exe):
        return exe
    exe = shutil.which("linxiv-cli")
    if exe:
        return exe
    raise LinxivError("linxiv-cli binary not found (neither bundled nor on PATH)")


def _opts(**kv):
    """kwargs -> CLI flags: None/False skipped, True bare, lists spread after the flag."""
    out = []
    for k, v in kv.items():
        if v is None or v is False:
            continue
        flag = "--" + k.replace("_", "-")
        if v is True:
            out.append(flag)
        elif isinstance(v, (list, tuple)):
            out += [flag, *map(str, v)]
        else:
            out += [flag, str(v)]
    return out


class Linxiv:
    """Client for one linXiv library.

    data_dir: library location (sets LINXIV_DATA_DIR; default = OS app-data dir,
    i.e. the same library the desktop app uses).
    binary: explicit path to linxiv-cli (default: bundled, then PATH).
    """

    def __init__(self, data_dir=None, binary=None):
        self._exe = binary or _find_cli()
        self._env = None
        if data_dir is not None:
            self._env = {**os.environ, "LINXIV_DATA_DIR": str(data_dir)}

    def _run(self, *args, parse=True):
        try:
            p = subprocess.run(
                [self._exe, *map(str, args)],
                capture_output=True, text=True, encoding="utf-8", env=self._env,
            )
        except OSError as e:
            raise LinxivError(str(e)) from e
        if p.returncode != 0:
            # fail() prints {"error": msg} as the LAST stderr line; some commands
            # eprintln a diagnostic line before it
            err = p.stderr.strip()
            try:
                msg = json.loads(err.splitlines()[-1])["error"]
            except (ValueError, KeyError, TypeError, IndexError):
                msg = err or f"linxiv-cli exited {p.returncode}"
            raise LinxivError(msg)
        out = p.stdout.strip()
        if not parse:
            return out
        return json.loads(out) if out else None

    # -- search / fetch ----------------------------------------------------
    def search_papers(self, query, source="arxiv", max_results=10):
        return self._run("search", query, *_opts(source=source, max=max_results))

    def fetch_paper(self, source_id, source="arxiv"):
        out = self._run("fetch", source_id, *_opts(source=source), parse=False)
        if source == "arxiv":
            # arxiv fetch prints Markdown, not JSON; re-read the saved record.
            # Non-arxiv ids must NOT go through `paper get` (it assumes arxiv:).
            return self.get_paper(source_id)
        return json.loads(out) if out else None

    def resolve_doi(self, doi):
        return self._run("doi", "resolve", doi)

    def save_doi(self, doi):
        return self._run("doi", "save", doi)

    # -- papers --------------------------------------------------------------
    def list_papers(self, limit=None, offset=0, category=None):
        return self._run("list", *_opts(limit=limit, offset=offset, category=category))

    def get_paper(self, source_id):
        return self._run("paper", "get", source_id)

    def search_local(self, query, limit=50):
        return self._run("paper", "search", query, *_opts(limit=limit))

    def get_paper_versions(self, source_id):
        return self._run("paper", "versions", source_id)

    def repair_paper(self, source_id, title, authors, published, summary=None,
                     category=None, doi=None, url=None, tags=None):
        return self._run(
            "paper", "repair", source_id,
            *_opts(title=title, authors=list(authors), published=published,
                   summary=summary, category=category, doi=doi, url=url, tags=tags),
        )

    def delete_paper(self, source_id):
        return self._run("paper", "delete", source_id)

    def restore_paper(self, source_id):
        return self._run("paper", "restore", source_id)

    def hard_delete_paper(self, source_id):
        return self._run("paper", "hard-delete", source_id)

    def remove_paper_from_all_projects(self, source_id):
        return self._run("paper", "remove-from-all-projects", source_id)

    # -- tags ----------------------------------------------------------------
    def add_tags_to_paper(self, source_id, *tags):
        return self._run("tag", "add", source_id, *tags)

    def remove_tags_from_paper(self, source_id, *tags):
        return self._run("tag", "remove", source_id, *tags)

    def get_paper_tags(self, source_id):
        return self._run("tag", "list", source_id)

    def list_all_tags(self):
        return self._run("tag", "list-all")

    def create_tag(self, label):
        return self._run("tag", "create", label)

    def delete_tag(self, tag_id):
        return self._run("tag", "delete", tag_id)

    def add_tags_to_project(self, project_id, *tags):
        return self._run("tag", "add-project", project_id, *tags)

    def remove_tags_from_project(self, project_id, *tags):
        return self._run("tag", "remove-project", project_id, *tags)

    def get_project_tags(self, project_id):
        return self._run("tag", "list-project", project_id)

    # -- projects ------------------------------------------------------------
    def list_projects(self, status=None):
        return self._run("project", "list", *_opts(status=status))

    def get_project(self, project_id):
        return self._run("project", "get", project_id)

    def create_project(self, name, description=None, color=None, tags=None):
        return self._run("project", "create", name,
                         *_opts(description=description, color=color, tags=tags))

    def update_project(self, project_id, name=None, description=None, color=None,
                       tags=None, status=None):
        return self._run("project", "update", project_id,
                         *_opts(name=name, description=description, color=color,
                                tags=tags, status=status))

    def delete_project(self, project_id):
        return self._run("project", "delete", project_id)

    def archive_project(self, project_id):
        return self._run("project", "archive", project_id)

    def restore_project(self, project_id):
        return self._run("project", "restore", project_id)

    def hard_delete_project(self, project_id):
        return self._run("project", "hard-delete", project_id)

    def add_paper_to_project(self, project_id, source_id):
        return self._run("project", "add-paper", project_id, source_id)

    def remove_paper_from_project(self, project_id, source_id):
        return self._run("project", "remove-paper", project_id, source_id)

    def export_project(self, project_id, dest, pdfs=False):
        return self._run("project", "export", project_id, dest, *_opts(pdfs=pdfs))

    def import_project(self, zip_path, preview=False, on_conflict=None):
        return self._run("project", "import", zip_path,
                         *_opts(preview=preview, on_conflict=on_conflict))

    def export_project_bibtex(self, project_id, dest):
        return self._run("project", "export-bibtex", project_id, dest)

    def export_project_obsidian(self, project_id, dest):
        return self._run("project", "export-obsidian", project_id, dest)

    # -- notes -----------------------------------------------------------
    def create_note(self, source_id, content, title=None, project_id=None):
        return self._run("note", "create", source_id, content,
                         *_opts(title=title, project_id=project_id))

    def get_note(self, note_id):
        return self._run("note", "get", note_id)

    def list_notes(self, paper_id=None, project_id=None):
        return self._run("note", "list", *_opts(paper_id=paper_id, project_id=project_id))

    def update_note(self, note_id, title=None, content=None):
        return self._run("note", "update", note_id, *_opts(title=title, content=content))

    def delete_note(self, note_id):
        return self._run("note", "delete", note_id)

    # -- annotations -------------------------------------------------------
    def create_annotation(self, source_id, anchor, comment=None, project_id=None):
        if not isinstance(anchor, str):
            anchor = json.dumps(anchor)
        return self._run("annotation", "create", source_id, anchor,
                         *_opts(comment=comment, project_id=project_id))

    def get_annotation(self, annotation_id):
        return self._run("annotation", "get", annotation_id)

    def list_annotations(self, paper_id=None, project_id=None):
        return self._run("annotation", "list",
                         *_opts(paper_id=paper_id, project_id=project_id))

    def update_annotation(self, annotation_id, comment):
        return self._run("annotation", "update", annotation_id, *_opts(comment=comment))

    def delete_annotation(self, annotation_id):
        return self._run("annotation", "delete", annotation_id)

    # -- pdfs ------------------------------------------------------------
    def get_pdf_path(self, source_id, version=None):
        return self._run("pdf", "path", source_id, *_opts(version=version))

    def download_pdf(self, source_id, url, version=None):
        return self._run("pdf", "download", source_id, url, *_opts(version=version))

    def get_pdf_storage(self):
        return self._run("pdf", "storage")

    def import_pdf(self, file, project_id=None):
        return self._run("pdf", "import", file, *_opts(project_id=project_id))

    def import_bibtex(self, file, project_id=None):
        return self._run("bibtex", "import", file, *_opts(project_id=project_id))

    # -- trash -----------------------------------------------------------
    def list_trash(self):
        return self._run("trash", "list")

    def trash_restore_paper(self, source_id):
        return self._run("trash", "restore", source_id)

    def trash_hard_delete_paper(self, source_id):
        return self._run("trash", "hard-delete", source_id)

    def restore_project_from_trash(self, project_id):
        return self._run("trash", "restore-project", project_id)

    def hard_delete_project_from_trash(self, project_id):
        return self._run("trash", "hard-delete-project", project_id)

    # -- authors -----------------------------------------------------------
    def list_authors(self):
        return self._run("author", "list")

    def get_author(self, author_id):
        return self._run("author", "get", author_id)

    def update_author(self, author_id, full_name=None, first_name=None,
                      last_name=None, orcid=None):
        return self._run("author", "update", author_id,
                         *_opts(full_name=full_name, first_name=first_name,
                                last_name=last_name, orcid=orcid))

    def delete_author(self, author_id):
        return self._run("author", "delete", author_id)

    # -- library ---------------------------------------------------------
    def get_stats(self):
        return self._run("stats")

    def list_categories(self):
        return self._run("categories")

    def get_settings(self):
        return self._run("settings", "get")

    def update_setting(self, key, value):
        if not isinstance(value, str):
            value = json.dumps(value)  # CLI JSON-parses valid JSON values
        return self._run("settings", "update", key, value)

    def backup(self, dest):
        return self._run("backup", dest)

    def restore_backup(self, src):
        return self._run("restore", src)
