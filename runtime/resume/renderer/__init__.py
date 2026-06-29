"""runtime.resume.renderer -- Renderer package.

Re-exports the Renderer ABC. Concrete renderers (Markdown, JSON Resume, HTML)
are implemented in separate modules and registered by the pipeline.
"""
from runtime.resume.renderer.base import Renderer

__all__ = ["Renderer"]
