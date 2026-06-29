"""runtime.resume -- Resume Assembly Engine.

Per user directive (Sprint 5 review):
    Resume is just a projection of the Career Knowledge Base.

    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

No LLM in this pipeline. The assembly is pure rules (keyword matching,
scoring, layout constraints). LLM is only used for optional bullet rewriting,
which goes through the Sprint 4 Draft -> Validator pattern.

Tailoring produces a ResumeIR, NEVER modifies Knowledge.
"""
from runtime.resume.ir import (
    ResumeIR,
    ResumeSection,
    ResumeItem,
    ResumeExplanation,
)
from runtime.resume.renderer.base import Renderer
from runtime.resume.selector import Selector
from runtime.resume.ranker import Ranker
from runtime.resume.layout import Layout
from runtime.resume.pipeline import ResumeAssemblyPipeline
from runtime.resume.tailoring import Tailoring
from runtime.resume.review import ResumeReview

__all__ = [
    "ResumeIR",
    "ResumeSection",
    "ResumeItem",
    "ResumeExplanation",
    "Renderer",
    "Selector",
    "Ranker",
    "Layout",
    "ResumeAssemblyPipeline",
    "Tailoring",
    "ResumeReview",
]
