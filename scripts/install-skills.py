#!/usr/bin/env python3
"""Install ResumeOS Skills into the current AI agent environment.

Auto-detects the AI agent (Claude Code, OpenCode, Cursor, or generic),
creates the correct skills directory, and symlinks (or copies on Windows)
each ResumeOS Skill so the agent can discover and use them.

Usage:
    python scripts/install-skills.py           # install all 9 skills
    python scripts/install-skills.py --list    # list available skills
    python scripts/install-skills.py resume_tailoring cover_letter  # install specific skills
    python scripts/install-skills.py --remove  # remove all ResumeOS skills

Run this from the repository root.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# --- Configuration ---------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SOURCE = REPO_ROOT / "skills"
REGISTRY_FILE = SKILLS_SOURCE / "registry.yaml"

# Agent-specific skill directories (relative to the agent's project root,
# which is typically the parent or current working directory).
AGENT_DIRS = {
    "claude": ".claude/skills",        # Claude Code
    "opencode": ".opencode/skills",    # OpenCode
    "cursor": ".cursor/skills",        # Cursor (custom convention)
    "generic": ".agent/skills",        # Generic fallback
}

# ---------------------------------------------------------------------------
# Skill registry parsing (lightweight YAML read — no PyYAML needed)
# ---------------------------------------------------------------------------

def list_skills() -> list[dict]:
    """Read skills/registry.yaml and return skill info."""
    skills: list[dict] = []
    if not REGISTRY_FILE.exists():
        return skills
    current: dict = {}
    for line in REGISTRY_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- name:"):
            if current:
                skills.append(current)
            current = {"name": stripped.split(":", 1)[1].strip().strip('"')}
        elif ":" in stripped and current:
            key, val = stripped.split(":", 1)
            current[key.strip()] = val.strip().strip('"')
    if current:
        skills.append(current)
    return skills


# ---------------------------------------------------------------------------
# Agent detection
# ---------------------------------------------------------------------------

def detect_agent(workspace: Path) -> str:
    """Detect which AI agent environment we are in.

    Checks for the existence of agent-specific directories or config files
    in the workspace root. Falls back to 'generic' if none match.
    """
    # Claude Code: look for .claude/ directory or CLAUDE.md
    if (workspace / ".claude").exists() or (workspace / "CLAUDE.md").exists():
        return "claude"

    # OpenCode: look for .opencode/ directory or opencode.json/jsonc
    if (workspace / ".opencode").exists():
        return "opencode"
    if (workspace / "opencode.json").exists() or (workspace / "opencode.jsonc").exists():
        return "opencode"

    # Cursor: look for .cursor/ directory
    if (workspace / ".cursor").exists():
        return "cursor"

    return "generic"


def find_workspace_root() -> Path:
    """Find the workspace root by looking for agent markers.

    Walks up from the repo root (or CWD) to find a directory that contains
    agent-specific markers. If none found, uses the repo root itself.
    """
    # Start from repo root and walk up
    current = REPO_ROOT
    while current != current.parent:
        for marker in [".claude", ".opencode", ".cursor", "CLAUDE.md",
                       "opencode.json", "opencode.jsonc"]:
            if (current / marker).exists():
                return current
        current = current.parent

    # No agent marker found — use repo root as workspace
    return REPO_ROOT


# ---------------------------------------------------------------------------
# Skill installation
# ---------------------------------------------------------------------------

def install_skill(skill_name: str, target_dir: Path, copy: bool = False) -> bool:
    """Install a single skill into target_dir.

    Uses symlink on Unix, copy on Windows (symlinks require admin).
    Returns True if installed, False if already exists or source missing.
    """
    source = SKILLS_SOURCE / skill_name
    if not source.exists():
        print(f"  [SKIP] {skill_name}: source not found at {source}")
        return False

    target = target_dir / skill_name
    if target.exists() or target.is_symlink():
        print(f"  [EXISTS] {skill_name}: already at {target}")
        return False

    target_dir.mkdir(parents=True, exist_ok=True)

    if copy or os.name == "nt":
        # Windows: copy (symlinks need admin privileges)
        shutil.copytree(source, target)
        print(f"  [COPIED] {skill_name} -> {target}")
    else:
        # Unix: symlink (efficient, auto-updates)
        os.symlink(source, target, target_is_directory=True)
        print(f"  [LINKED] {skill_name} -> {target}")

    return True


def remove_skill(skill_name: str, target_dir: Path) -> bool:
    """Remove a skill from target_dir."""
    target = target_dir / skill_name
    if not target.exists() and not target.is_symlink():
        return False

    if target.is_symlink():
        os.unlink(target)
    else:
        shutil.rmtree(target)
    print(f"  [REMOVED] {skill_name} from {target}")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install ResumeOS Skills into your AI agent environment."
    )
    parser.add_argument(
        "skills",
        nargs="*",
        help="Skill names to install (default: all). Use --list to see available.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available skills and exit.",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove all ResumeOS skills from the agent directory.",
    )
    parser.add_argument(
        "--agent",
        choices=["claude", "opencode", "cursor", "generic"],
        help="Force a specific agent type (auto-detected by default).",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        help="Workspace root path (auto-detected by default).",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of symlinking (default on Windows).",
    )
    args = parser.parse_args()

    # --list
    if args.list:
        skills = list_skills()
        if not skills:
            print("No skills found in registry.")
            return 1
        print(f"Available skills ({len(skills)}):")
        for s in skills:
            desc = s.get("description", "")
            ver = s.get("version", "")
            print(f"  {s['name']:25s} v{ver:8s}  {desc}")
        return 0

    # Determine workspace and agent
    workspace = Path(args.workspace) if args.workspace else find_workspace_root()
    agent = args.agent or detect_agent(workspace)
    agent_dir_rel = AGENT_DIRS[agent]
    target_dir = workspace / agent_dir_rel

    print(f"ResumeOS Skill Installer")
    print(f"  Agent type:    {agent}")
    print(f"  Workspace:     {workspace}")
    print(f"  Target dir:    {target_dir}")
    print(f"  Source:        {SKILLS_SOURCE}")
    print()

    # --remove
    if args.remove:
        skills = list_skills()
        removed = 0
        for s in skills:
            if remove_skill(s["name"], target_dir):
                removed += 1
        print(f"\nRemoved {removed} skill(s).")
        return 0

    # Determine which skills to install
    all_skills = list_skills()
    if not all_skills:
        print("ERROR: No skills found in registry.yaml.")
        return 1

    if args.skills:
        skill_names = args.skills
        # Validate
        valid_names = {s["name"] for s in all_skills}
        invalid = set(skill_names) - valid_names
        if invalid:
            print(f"ERROR: Unknown skill(s): {', '.join(invalid)}")
            print(f"Available: {', '.join(valid_names)}")
            return 1
    else:
        skill_names = [s["name"] for s in all_skills]

    # Install
    print(f"Installing {len(skill_names)} skill(s)...\n")
    installed = 0
    for name in skill_names:
        if install_skill(name, target_dir, copy=args.copy):
            installed += 1

    print(f"\nDone: {installed} installed, {len(skill_names) - installed} skipped.")

    # Post-install guidance
    print(f"\n{'=' * 60}")
    print(f"Skills installed to: {target_dir}")
    print(f"{'=' * 60}")
    if agent == "claude":
        print(f"\nClaude Code will auto-discover skills in {agent_dir_rel}/.")
        print(f"Restart Claude Code or run /skills to see them.")
    elif agent == "opencode":
        print(f"\nOpenCode will auto-discover skills in {agent_dir_rel}/.")
        print(f"Restart OpenCode or check skill list to verify.")
    elif agent == "cursor":
        print(f"\nCursor: you may need to restart the editor for skills to load.")
    else:
        print(f"\nGeneric agent: point your AI tool at {target_dir}.")

    print(f"\nVerify: ls {target_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
