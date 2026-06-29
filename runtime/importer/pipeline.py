"""Stage 4 / orchestration: ImporterPipeline.

The ImporterPipeline wires together Detector -> Extractor -> Normalizer
and produces the final Artifact. This is the only public entrypoint
a Skill or the CLI should call::

    pipeline = ImporterPipeline()
    artifact = pipeline.run(Path("inbox/my_resume.pdf"))

Pipeline behaviour (Sprint 2.5):

1. Hash the original file exactly once via
   ArtifactProvenance.hash_file(path). For git repositories (which are
   directories, not files), we hash the HEAD commit SHA.
2. Run MimeDetector -> DetectionResult.
3. Select an extractor from ImporterRegistry via the detected kind.
4. Run the extractor -> raw fields dict.
5. Build an ArtifactProvenance and pass it to the Normalizer along with
   the detection + fields.
6. Return the Artifact.

If detection yields 'unknown', or no extractor is registered for the
kind, the pipeline raises ImportError. The caller is expected to route
that to vault/inbox/_errors/ with a stub note (ADR-0019).
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Optional

from runtime.artifacts.base import Artifact, ArtifactProvenance
from runtime.importer.detector import DetectionResult, Detector, MimeDetector
from runtime.importer.extractor import Extractor
from runtime.importer.normalizer import Normalizer
from runtime.importer.registry import ImporterRegistry


class ImporterPipeline:
    """Orchestrates: Detector -> Extractor -> Normalizer -> Artifact."""

    def __init__(
        self,
        detector: Optional[Detector] = None,
        registry: Optional[ImporterRegistry] = None,
    ):
        self.detector = detector or MimeDetector()
        self.registry = registry or ImporterRegistry()

    def run(self, path: Path) -> Artifact:
        """Run the full pipeline on `path`."""
        path = Path(path)

        # 1. Detect
        detection = self.detector.detect(path)
        if detection.detected_type == "unknown":
            raise ImportError(
                f"unsupported file type: {detection.detected_type}"
            )

        # 2. Resolve registry kind
        kind = self._resolve_kind(detection, path)
        try:
            extractor = self.registry.get_extractor(kind)
        except KeyError as e:
            raise ImportError(
                f"unsupported file type: {detection.detected_type}"
            ) from e

        # 3. Extract (zero-AI)
        try:
            fields = extractor.extract(path, detection)
        except Exception as exc:
            raise ImportError(
                f"extractor failed for {path}: {exc}"
            ) from exc

        # 4. Provenance (hash)
        source_hash = self._hash_path(path)
        provenance = ArtifactProvenance(
            source_path=str(path),
            sha256=source_hash,
            detected_type=detection.detected_type,
            extractor=kind,
        )

        # 5. Normalize into Artifact
        normalizer = Normalizer(provenance=provenance)
        artifact = normalizer.normalize(detection, fields)

        return artifact

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_kind(self, detection: DetectionResult, path: Path) -> str:
        # MimeDetector returns 'git_repository', registry uses 'git'.
        # For other types, detector string and registry kind match
        # directly for the 5 types shipped in Sprint 2.5.
        if detection.detected_type == "git_repository":
            return "git"
        return detection.detected_type

    def _hash_path(self, path: Path) -> str:
        """Compute a deterministic hash of the source.

        Files are hashed directly by their bytes. Directories (git
        repositories) are hashed via their HEAD commit SHA to keep
        the hash deterministic across runs without hashing every file.
        """
        if path.is_dir():
            return self._hash_git_repo(path)
        return ArtifactProvenance.hash_file(path)

    def _hash_git_repo(self, path: Path) -> str:
        """Deterministic hash for a git repo (HEAD commit SHA)."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(path),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                commit_sha = res.stdout.strip().encode("utf-8")
                return hashlib.sha256(commit_sha).hexdigest()
        except Exception:
            pass

        # Fallback: hash the absolute directory path (deterministic per
        # machine/path) so tests don't crash if git is missing.
        return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
