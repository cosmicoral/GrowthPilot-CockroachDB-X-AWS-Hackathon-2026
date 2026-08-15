from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


MemoryType = Literal[
    "episodic",
    "semantic",
    "user",
    "task",
    "reflection",
]


class MemoryCandidate(BaseModel):
    """A candidate memory selected from an interaction."""

    content: str = Field(min_length=1)
    memory_type: MemoryType
    importance: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, object] = Field(default_factory=dict)


class MemoryExtractionResult(BaseModel):
    """Validated result of memory extraction."""

    memories: list[MemoryCandidate] = Field(default_factory=list)


SYSTEM_PROMPT = """
You extract long-term memories from GrowthPilot conversations.

Store only information that is likely to be useful in future interactions.

REMEMBER:
- durable user or founder preferences
- durable company or business context
- important decisions or commitments
- meaningful discoveries
- important completed events
- useful reflections or lessons
- persistent project/task context

IGNORE:
- greetings and small talk
- conversational filler
- temporary logistics
- one-off requests with no lasting value
- irrelevant details
- information explicitly superseded by newer information
- sensitive/private information that is not necessary for future work

MEMORY TYPES:
- user: durable user/founder preference or characteristic
- semantic: durable fact, business context, or discovery
- episodic: significant event or completed action
- task: persistent project/task context
- reflection: meaningful lesson, conclusion, or strategic insight

IMPORTANCE:
Use 0.0 to 1.0 based on expected future usefulness.
Use high values only for information that materially affects future agent behavior.

METADATA:
Keep metadata minimal and useful. Do not copy conversation content into metadata.

CONTENT:
Make each memory concise and self-contained.
Create separate memories for distinct durable facts.
Never store the entire conversation.

Return JSON only:

{
  "memories": [
    {
      "content": "...",
      "memory_type": "user|semantic|episodic|task|reflection",
      "importance": 0.0,
      "metadata": {}
    }
  ]
}

If nothing deserves long-term storage, return:

{"memories": []}
""".strip()


class MemoryExtractionPolicy:
    """Decides which interaction details deserve long-term memory."""

    def __init__(self, bedrock_client):
        self.bedrock_client = bedrock_client

    async def extract(self, text: str) -> MemoryExtractionResult:
        if not text.strip():
            return MemoryExtractionResult()

        response = await self.bedrock_client.generate_text(
            prompt = text,
            system_prompt = SYSTEM_PROMPT,
            max_tokens = 1000,
            temperature = 0.0,
        )

        try:
            data = json.loads(response)
            return MemoryExtractionResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise ValueError(
                "Memory extraction returned invalid structured output"
            ) from exc