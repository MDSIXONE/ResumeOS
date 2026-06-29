"""Renderer ABC -- converts ResumeIR to an output format.

Per user directive (Sprint 5): Resume is a projection of Knowledge.
ResumeIR is the intermediate; Renderer is the final step.

    ResumeIR -> Renderer -> Markdown / JSON Resume / HTML / PDF / DOCX

Renderer does NOT know about:
    - Knowledge (it only sees ResumeIR)
    - LLM (no LLM in the assembly pipeline)
    - Selector / Ranker / Layout (those produce ResumeIR, Renderer consumes it)

Adding a new output format = adding a new Renderer subclass.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from runtime.resume.ir import ResumeIR


class Renderer(ABC):
    """Base class for all resume renderers.

    A Renderer converts a ResumeIR into a specific output format.
    Each format (Markdown, JSON Resume, HTML, PDF, DOCX) is a separate subclass.
    """

    @abstractmethod
    def render(self, ir: ResumeIR) -> str:
        """Render ResumeIR to a string in the output format.

        Args:
            ir: The ResumeIR to render.

        Returns:
            The rendered content as a string (e.g. Markdown text, JSON string, HTML).
        """
        ...

    @abstractmethod
    def file_extension(self) -> str:
        """Return the output file extension (without dot), e.g. 'md', 'json', 'html'."""
        ...

    @abstractmethod
    def format_name(self) -> str:
        """Return the human-readable format name, e.g. 'Markdown', 'JSON Resume', 'HTML'."""
        ...

    def render_to_file(self, ir: ResumeIR, path: Path) -> None:
        """Render the ResumeIR and write the result to a file.

        Creates parent directories if they don't exist.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = self.render(ir)
        p.write_text(content, encoding="utf-8")

    def render_to_dir(self, ir: ResumeIR, output_dir: Path, filename: str = "") -> Path:
        """Render to a directory with an auto-generated filename.

        Args:
            ir: The ResumeIR to render.
            output_dir: Directory to write the file in.
            filename: Base filename (without extension). If empty, uses ir.ir_id.

        Returns:
            The path to the written file.
        """
        base = filename or ir.ir_id
        ext = self.file_extension()
        path = Path(output_dir) / f"{base}.{ext}"
        self.render_to_file(ir, path)
        return path
