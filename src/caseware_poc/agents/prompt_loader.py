from __future__ import annotations

from pathlib import Path

from caseware_poc.guardrails.markdown_assets import load_markdown_asset


class PromptAssetLoader:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.guardrails_dir = repo_root / "guardrails"
        self.skills_dir = self.guardrails_dir / "skills"
        self.rules_dir = self.guardrails_dir / "rules"
        self.templates_dir = self.guardrails_dir / "templates"
        self.context_file = self.guardrails_dir / "context" / "system_context.txt"

    def load_skill(self, skill_name: str) -> str:
        path = self.skills_dir / f"{skill_name}.md"
        payload, body = load_markdown_asset(path)
        title = str(payload.get("title", skill_name)).strip()
        return f"{title}\n\n{body}".strip() if body else title

    def load_rules(self, rules_name: str) -> dict:
        if rules_name == "llm_guardrails":
            return {
                "routing": load_markdown_asset(self.rules_dir / "routing.md")[0]["routing"],
                "retrieval": load_markdown_asset(self.rules_dir / "retrieval.md")[0]["retrieval"],
                "response": load_markdown_asset(self.rules_dir / "response.md")[0]["response"],
            }
        path = self.rules_dir / f"{rules_name}.md"
        payload, _ = load_markdown_asset(path)
        return payload

    def load_template(self, template_name: str) -> str:
        suffix = ".sql" if template_name.endswith("_query") else ".txt"
        path = self.templates_dir / f"{template_name}{suffix}"
        return path.read_text(encoding="utf-8")

    def load_system_context(self) -> str:
        return self.context_file.read_text(encoding="utf-8")
