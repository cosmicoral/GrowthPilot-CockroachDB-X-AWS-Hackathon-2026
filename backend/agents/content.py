import logging

from backend.agents.base import Agent
from backend.memory.store import MemoryHit

logger = logging.getLogger(__name__)

class ContentAgent(Agent):
    """
    Agent for generating Go-To-Market content (e.g., social posts, outreach).
    It grounds the content in the founder's existing memory context.
    """

    def __init__(self, context):
        super().__init__(context)
        self.retrieved_memories: list[MemoryHit] = []

    @property
    def name(self) -> str:
        return "content"

    async def retrieve_memories(self, prompt: str, **kwargs) -> list[MemoryHit]:
        """
        Retrieve relevant context from the MemoryStore before generation.
        We search for episodic, semantic, and user preferences.
        """
        logger.info(f"Retrieving memory context for prompt: {prompt}")
        
        try:
            # Search memory store for context related to the user's prompt
            memories = await self.context.memory_repository.search(
                company_id=self.context.company_id,
                query=prompt,
                k=5,
                types=["episodic", "semantic", "user", "task", "reflection"]
            )
            self.retrieved_memories = memories
            return memories
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            # Handle gracefully by returning empty context rather than crashing
            self.retrieved_memories = []
            return []

    async def process(self, retrieved_memories: list[MemoryHit], prompt: str, **kwargs) -> str:
        """
        Generate content using AWS Bedrock based on the prompt and retrieved context.
        """
        # Compile retrieved memories into a context string
        context_text = ""
        if retrieved_memories:
            context_pieces = [f"- {m.content}" for m in retrieved_memories]
            context_text = "\n".join(context_pieces)
        else:
            context_text = "No specific background context found. Rely on general best practices."

        system_prompt = (
            "You are an expert Go-To-Market content creator. "
            "Your goal is to write high-converting, engaging social media "
            "posts or outreach messages for a startup founder.\n\n"
            "Below is the relevant background context about the founder's "
            "startup, market, and preferences:\n"
            "<context>\n"
            f"{context_text}\n"
            "</context>\n\n"
            "Generate the requested content incorporating this context naturally. "
            "Do not sound robotic or generic. Match the founder's tone."
        )

        logger.info("Generating content via Bedrock LLM client")
        generated_content = await self.context.bedrock_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000,
            temperature=0.7
        )

        return generated_content

    async def persist_memories(self, result_data: str) -> None:
        """
        Optionally persist generated content back into memory for iteration/history.
        """
        logger.info("Persisting generated content to MemoryStore as a task memory.")
        try:
            await self.context.memory_repository.write(
                company_id=self.context.company_id,
                memory_type="task",
                content=f"Generated Content:\n{result_data}",
                metadata={"agent": self.name},
                importance=0.6
            )
        except Exception as e:
            logger.error(f"Failed to persist generated content to memory: {e}")
