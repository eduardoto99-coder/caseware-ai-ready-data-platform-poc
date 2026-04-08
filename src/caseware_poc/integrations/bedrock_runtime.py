from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import boto3


@dataclass(slots=True)
class BedrockRuntimeConfig:
    region_name: str
    model_id: str = "anthropic.claude-3-7-sonnet-20250219-v1:0"


class BedrockAnswerSynthesizer:
    """Small Bedrock wrapper used by the agent workflow."""

    def __init__(self, config: BedrockRuntimeConfig) -> None:
        self.config = config
        self.client = boto3.client("bedrock-runtime", region_name=config.region_name)

    def generate_grounded_answer(
        self,
        *,
        system_prompt: str,
        user_question: str,
        structured_context: list[dict[str, Any]],
        retrieved_context: list[dict[str, Any]],
        guardrail_rules: dict[str, Any],
    ) -> dict[str, Any]:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"Question:\n{user_question}\n\n"
                            f"Guardrail rules:\n{guardrail_rules}\n\n"
                            f"Structured SQL context:\n{structured_context}\n\n"
                            f"Retrieved context:\n{retrieved_context}"
                        )
                    }
                ],
            }
        ]
        return self.client.converse(
            modelId=self.config.model_id,
            system=[{"text": system_prompt}],
            messages=messages,
            inferenceConfig={
                "maxTokens": 1200,
                "temperature": 0.0,
            },
        )
