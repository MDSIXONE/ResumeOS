"""Bundled zero-AI extractors for Sprint 2.5.

Each module exposes a single :class:`Extractor` subclass:

- :mod:`pdf_text`     — :class:`PDFTextExtractor`
- :mod:`docx_text`    — :class:`DOCXTextExtractor`
- :mod:`readme_parser`— :class:`READMEExtractor`
- :mod:`git_log`      — :class:`GitExtractor`
- :mod:`image_exif`   — :class:`ImageExtractor`

Importing this package does NOT import any concrete extractor eagerly;
each extractor imports its heavy dep (``pypdf``, ``docx``, ``PIL``)
lazily inside :meth:`extract` to keep CLI startup fast and keep the
dependency check in tests simple.
"""

from __future__ import annotations
