"""ResumeOS adapters -- concrete implementations of runtime interfaces.

Adapters are DOWNSTREAM of runtime:
    runtime/ defines ABCs (LLMProvider, KnowledgeWriter, ...)
    adapters/ provides concrete implementations (ClaudeProvider, ...)

Dependency direction:
    adapters/ -> runtime/   (OK)
    runtime/ -> adapters/   (FORBIDDEN -- CI-enforced)
"""
