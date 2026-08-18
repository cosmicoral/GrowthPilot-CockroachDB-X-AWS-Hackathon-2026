from pathlib import Path
from typing import Optional
from uuid import UUID

from backend.agents.skills.loader import SkillLoader
from backend.agents.trace import TraceRepository
from backend.llm.client import BedrockClient
from backend.memory.repository import MemoryRepository


class AgentContext:
    """
    Shared execution context for agents.

    Provides common resources like Bedrock LLM client, Memory Repository,
    Trace Repository, Skill Loader, and company configuration parameters
    required for agent execution.
    """

    def __init__(
        self,
        company_id: UUID,
        bedrock_client: BedrockClient,
        memory_repository: MemoryRepository,
        trace_repository: Optional[TraceRepository] = None,
    ):
        self.company_id = company_id
        self.bedrock_client = bedrock_client
        self.memory_repository = memory_repository
        self.trace_repository = trace_repository or TraceRepository()

        skills_dir = Path(__file__).parent / "skills"
        self.skill_loader = SkillLoader(skills_dir)