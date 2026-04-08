from __future__ import annotations

from pathlib import Path

import yaml


class PromptAssetLoader:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.guardrails_dir = repo_root / "guardrails"
        self.skills_dir = self.guardrails_dir / "skills"
        self.rules_dir = self.guardrails_dir / "rules"
        self.templates_dir = self.guardrails_dir / "templates"
        self.context_file = self.guardrails_dir / "context" / "system_context.md"

    def load_skill(self, skill_name: str) -> str:
        path = self.skills_dir / f"{skill_name}.md"
        return path.read_text(encoding="utf-8")

    def load_rules(self, rules_name: str) -> dict:
        if rules_name == "llm_guardrails":
            return {
                "routing": yaml.safe_load((self.rules_dir / "routing.yaml").read_text(encoding="utf-8"))["routing"],
                "retrieval": yaml.safe_load((self.rules_dir / "retrieval.yaml").read_text(encoding="utf-8"))[
                    "retrieval"
                ],
                "response": yaml.safe_load((self.rules_dir / "response.yaml").read_text(encoding="utf-8"))[
                    "response"
                ],
            }
        path = self.rules_dir / f"{rules_name}.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def load_template(self, template_name: str) -> str:
        suffix = ".sql" if template_name.endswith("_query") else ".md"
        path = self.templates_dir / f"{template_name}{suffix}"
        return path.read_text(encoding="utf-8")

    def load_system_context(self) -> str:
        return self.context_file.read_text(encoding="utf-8")
