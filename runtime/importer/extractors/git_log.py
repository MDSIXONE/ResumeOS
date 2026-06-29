"""Git repository extractor — zero-AI, subprocess to git only.

Runs a handful of read-only ``git`` subcommands via ``subprocess.run``
and collects:

- commit count (``git log --format=%H``)
- remote URL (``git remote -v`` — first fetch entry)
- languages detected from file extensions in ``git ls-files``

All subprocess calls use ``capture_output=True, text=True, timeout=10``
and degrade gracefully: if ``git`` is not installed, the cwd is not a
git repo, or a command times out, the extractor returns empty fields
plus a note rather than raising.

No LLM. No git remote writes. Read-only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List

from runtime.importer.detector import DetectionResult
from runtime.importer.extractor import Extractor


# Map file extension → language name. Deliberately small — we only need
# the high-signal languages that ResumeOS users typically have on their
# resumes. Downstream Skills can refine.
EXT_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".go": "Go",
    ".rs": "Rust",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cxx": "C++", ".cc": "C++",
    ".hpp": "C++", ".hxx": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".sh": "Shell", ".bash": "Shell",
    ".md": "Markdown",
}


def _git(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run a git command, never raise on failure — always return a result."""
    try:
        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True, text=True, timeout=10,
            check=False,
        )
    except FileNotFoundError:
        # git not installed
        return subprocess.CompletedProcess(
            args=["git", *args], returncode=-1,
            stdout="", stderr="git executable not found",
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=["git", *args], returncode=-2,
            stdout="", stderr="git command timed out",
        )


class GitExtractor(Extractor):
    """Run ``git`` commands and return commit/remote/language data."""

    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Return ``{commit_count, repo_url, languages, notes}``."""
        path = Path(path)
        notes: List[str] = []

        # --- commits -----------------------------------------------------
        commit_count = 0
        r = _git(["log", "--format=%H"], cwd=path)
        if r.returncode == 0:
            commit_count = len([ln for ln in r.stdout.splitlines() if ln.strip()])
        else:
            notes.append(f"git log failed: {r.stderr.strip() or 'no commits'}")

        # --- remote URL --------------------------------------------------
        repo_url = ""
        r = _git(["remote", "-v"], cwd=path)
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                # Format: "<name>\t<url> (<action>)"
                if "(fetch)" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        repo_url = parts[1]
                        break
        else:
            notes.append(f"git remote -v failed: {r.stderr.strip()}")

        # --- languages from tracked files --------------------------------
        languages: List[str] = []
        seen: set = set()
        r = _git(["ls-files"], cwd=path)
        if r.returncode == 0:
            for filename in r.stdout.splitlines():
                if not filename:
                    continue
                ext = Path(filename).suffix.lower()
                lang = EXT_TO_LANG.get(ext)
                if lang and lang not in seen:
                    languages.append(lang); seen.add(lang)
            languages.sort()
        else:
            notes.append(f"git ls-files failed: {r.stderr.strip()}")

        return {
            "commit_count": commit_count,
            "repo_url": repo_url,
            "languages": languages,
            "notes": notes,
        }
