from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Skill:
    """A reusable Agent Skill loaded from a SKILL.md file."""

    name: str
    description: str
    instructions: str
    path: Path


class SkillLoader:
    """Discover and load Agent Skills from a local skills directory."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir

    def discover(self) -> list[str]:
        """Return the names of skill directories containing SKILL.md."""
        if not self.skills_dir.exists():
            return []

        return sorted(
            directory.name
            for directory in self.skills_dir.iterdir()
            if directory.is_dir() and (directory / "SKILL.md").is_file()
        )

    def load(self, name: str) -> Optional[Skill]:
        """Load a skill by name.

        Missing or invalid skills return None instead of crashing an agent.
        """
        skill_file = self.skills_dir / name / "SKILL.md"

        if not skill_file.is_file():
            return None

        try:
            content = skill_file.read_text(encoding="utf-8")
            frontmatter, instructions = self._parse_skill_file(content)

            skill_name = frontmatter.get("name")
            description = frontmatter.get("description")

            if not skill_name or not description:
                return None

            return Skill(
                name=skill_name,
                description=description,
                instructions=instructions.strip(),
                path=skill_file,
            )
        except (OSError, UnicodeError, ValueError):
            return None

    @staticmethod
    def _parse_skill_file(content: str) -> tuple[dict[str, str], str]:
        """Parse the simple YAML-style frontmatter used by SKILL.md."""
        if not content.startswith("---"):
            raise ValueError("Missing skill frontmatter")

        parts = content.split("---", 2)

        if len(parts) != 3:
            raise ValueError("Invalid skill frontmatter")

        _, frontmatter_text, instructions = parts

        frontmatter: dict[str, str] = {}

        for line in frontmatter_text.splitlines():
            line = line.strip()

            if not line or ":" not in line:
                continue

            key, value = line.split(":", 1)
            value = value.strip().strip("\"'")

            if key.strip() and value:
                frontmatter[key.strip()] = value

        return frontmatter, instructions