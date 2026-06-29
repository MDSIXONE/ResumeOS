"""README.md parser — zero-AI, regex only.

Extracts a project README's title, short description, detected
technology keywords, and the full raw text. No LLM, no external
parser — just a handful of regexes over the Markdown source.

Tech detection uses a curated keyword list (languages + common tools)
that covers the majority of ResumeOS target resumes. The list is
intentionally small and case-matched so we don't false-positive on
common English words (e.g. ``Go`` is matched only as the ``Go`` token,
and even then we accept some noise because downstream Skills refine).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from runtime.importer.detector import DetectionResult
from runtime.importer.extractor import Extractor


# Curated tech keyword list — case-insensitive scan, matched as whole words
# where the risk of false-positive is high (Go, R, C). Short tokens use
# `\b` word boundaries; longer tokens just need substring presence.
_TECH_KEYWORDS = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "Kotlin", "Swift",
    "C++", "C#", "Objective-C", "Rust", "Ruby", "PHP", "Scala",
    "MATLAB", "Julia", "Haskell", "Elixir", "Clojure",
    # Mobile / UI frameworks
    "React", "Angular", "Vue", "Next.js", "Svelte",
    # Backend / infra
    "Node", "Django", "Flask", "FastAPI", "Spring", "Express",
    "Docker", "Kubernetes", "Terraform", "Ansible",
    # Robotics / ML
    "ROS", "ROS2", "CMake", "TensorFlow", "PyTorch",
    "OpenCV", "CUDA", "ONNX",
    # Data
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
    "Kafka", "RabbitMQ",
    # Cloud
    "AWS", "Azure", "GCP",
    # Misc
    "Linux", "Git", "CI/CD", "REST", "GraphQL", "gRPC",
]

# For single-short-word keywords we require `\b` boundaries so we do
# not match "React" inside "reactive" or "Go" inside "Golang" — wait,
# "Golang" should NOT match "Go" (we want the language name explicit);
# but "Go" as a standalone token is fine.
_SHORT_TOKEN_BOUNDARY = {"Go", "R", "C", "V"}  # treated case-sensitively


def _detect_tech_stack(text: str) -> List[str]:
    """Return the detected tech-stack keywords in declaration order."""
    found: List[str] = []
    seen: set = set()
    for kw in _TECH_KEYWORDS:
        if kw in _SHORT_TOKEN_BOUNDARY:
            # Must be word-bounded and case-sensitive
            pattern = r"(?<![A-Za-z])" + re.escape(kw) + r"(?![A-Za-z])"
            if re.search(pattern, text):
                if kw not in seen:
                    found.append(kw); seen.add(kw)
        else:
            if kw in text and kw not in seen:
                found.append(kw); seen.add(kw)
    return found


_TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


class READMEExtractor(Extractor):
    """Parse a README.md into title + description + tech stack."""

    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Return ``{title, description, tech_stack, readme_text, notes}``."""
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {
                "title": "", "description": "", "tech_stack": [],
                "readme_text": "",
                "notes": [f"README read error: {exc}"],
            }

        title = ""
        m = _TITLE_RE.search(raw)
        if m:
            title = m.group(1).strip()

        # Description: first non-empty line after the title heading.
        description = ""
        in_body = False
        for line in raw.splitlines():
            if not in_body:
                if _TITLE_RE.match(line):
                    in_body = True
                continue
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                description = stripped
                break

        tech_stack = _detect_tech_stack(raw)
        notes: List[str] = []
        if not title:
            notes.append("README has no H1 heading")
        if not description:
            notes.append("README has no description paragraph after title")

        return {
            "title": title,
            "description": description,
            "tech_stack": tech_stack,
            "readme_text": raw,
            "notes": notes,
        }
