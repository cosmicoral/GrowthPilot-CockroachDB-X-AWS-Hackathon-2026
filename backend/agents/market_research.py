"""
Market Research Agent.

Pipeline: fetch → structure → dedup → embed → persist

Responsibilities:
1. Fetch: Gather raw market research (competitors, industry trends, customer pain points)
   for a founder's company/product using LLM generation or external research text.
2. Structure: Chunk raw research into memory-sized pieces, categorized by topic,
   with rich metadata (source, category, company_name, industry, trigger_source, timestamp).
3. Dedup: Deduplicate chunks using content hashing (create_content_hash)
   and DB-level ON CONFLICT / semantic deduplication.
4. Embed: Generate 1024-d vector embeddings using Bedrock embedding service (batched).
5. Persist: Write memories directly via MemoryRepository.save_memories_batch()
   with memory_type = "semantic".

Note: this agent talks to MemoryRepository directly rather than through
MemoryWriter, since it already knows exactly what memory_type/metadata/
importance each chunk should get — there's no LLM-driven extraction
decision to make here, just structured research output ready to persist.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from backend.agents.base import Agent
from backend.agents.context import AgentContext
from backend.memory.chunker import TextChunker
from backend.memory.embedding import BedrockEmbeddingService
from backend.memory.hash import create_content_hash

logger = logging.getLogger(__name__)

TriggerSource = Literal["onboarding", "manual", "periodic"]
ResearchCategory = Literal["competitors", "trends", "pain_points", "general"]


class MarketResearchAgent(Agent):
    """
    Backend agent for researching market context (competitors, trends, pain points)
    and persisting structured semantic memories.
    """

    def __init__(self, context: AgentContext):
        super().__init__(context)
        self.chunker = TextChunker()
        self.embedding_service = BedrockEmbeddingService(context.bedrock_client)

    @property
    def name(self) -> str:
        return "market_research"

    async def retrieve_memories(self, *args, **kwargs) -> List[Any]:
        """
        Hook to retrieve existing market research memories prior to execution,
        avoiding redundant work during periodic refreshes.
        """
        try:
            if hasattr(self.context.memory_repository, "recent"):
                existing = await self.context.memory_repository.recent(
                    company_id=self.context.company_id,
                    memory_type="semantic",
                    limit=20,
                )
                return [
                    m for m in existing
                    if getattr(m, "metadata", {}).get("source") == "market_research"
                ]
        except Exception as exc:
            logger.warning("Could not retrieve prior market research memories: %s", exc)
        return []

    async def process(self, retrieved_memories: Any, *args, **kwargs) -> Dict[str, Any]:
        """
        Execute core reasoning and research actions.

        Kwargs:
            company_profile: Dict with keys name, industry, description, website
            custom_research_text: Optional external raw research text
            trigger_source: "onboarding", "manual", or "periodic"
        """
        company_profile = kwargs.get("company_profile") or {}
        custom_research_text = kwargs.get("custom_research_text")
        research_request = kwargs.get("prompt", "")
        trigger_source: TriggerSource = kwargs.get("trigger_source", "manual")

        company_name = company_profile.get("name", "Company")
        industry = company_profile.get("industry", "Technology")
        description = company_profile.get("description", "")
        website = company_profile.get("website", "")

        # 1. Fetch Stage
        if custom_research_text and custom_research_text.strip():
            raw_research = custom_research_text.strip()
            content_origin = "user_supplied"
        else:
            prior_research = "\n".join(
                str(memory.content)
                for memory in (retrieved_memories or [])[:5]
                if getattr(memory, "content", None)
            )
            raw_research = await self._fetch_llm_research(
                company_name=company_name,
                industry=industry,
                description=description,
                website=website,
                research_request=research_request,
                prior_research=prior_research,
            )
            content_origin = "llm_generated"

        # 2. Structure Stage
        structured_chunks = self._structure_research(
            raw_research=raw_research,
            company_name=company_name,
            industry=industry,
            trigger_source=trigger_source,
            content_origin=content_origin,
        )

        return {
            "company_id": str(self.context.company_id),
            "company_name": company_name,
            "industry": industry,
            "trigger_source": trigger_source,
            "raw_research": raw_research,
            "structured_chunks": structured_chunks,
        }

    async def _fetch_llm_research(
        self,
        company_name: str,
        industry: str,
        description: str,
        website: str,
        research_request: str = "",
        prior_research: str = "",
    ) -> str:
        """
        Use Bedrock LLM to generate comprehensive market research across 3 core categories.
        """
        request_text = research_request.strip() or (
            "Produce a broad market intelligence update."
        )
        prior_context = prior_research.strip() or "No prior research available."

        prompt = (
            f"Conduct comprehensive market research for the following company:\n"
            f"Company Name: {company_name}\n"
            f"Industry: {industry}\n"
            f"Description: {description}\n"
            f"Website: {website}\n\n"
            f"Specific founder request: {request_text}\n\n"
            "Existing stored research (use it to avoid needless repetition "
            f"and identify changes):\n{prior_context}\n\n"
            "Provide detailed, actionable market research organized clearly "
            "under these three headings:\n"
            "1. COMPETITOR LANDSCAPE: Identify key direct and indirect "
            "competitors, positioning, strengths, weaknesses, and "
            "differentiators.\n"
            "2. INDUSTRY TRENDS: Identify major trends, market tailwinds, "
            "growth opportunities, and technological shifts.\n"
            "3. CUSTOMER PAIN POINTS: Identify target customer pain points, "
            "unmet needs, pricing friction, and workflow challenges.\n"
        )
        system_prompt = (
            "You are GrowthPilot's Senior Market Intelligence Agent. "
            "Generate structured, factual, and analytical market research."
        )

        return await self.context.bedrock_client.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.4,
        )

    def _structure_research(
        self,
        raw_research: str,
        company_name: str,
        industry: str,
        trigger_source: TriggerSource,
        content_origin: str = "llm_generated",
    ) -> List[Dict[str, Any]]:
        """
        Structure raw research text into memory-sized chunks with metadata.
        Categorizes chunks into competitors, trends, pain_points, or general.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        structured_items = []

        raw_sections = raw_research.split("\n\n")

        for section in raw_sections:
            section_clean = section.strip()
            if not section_clean:
                continue

            category = self._categorize_section(section_clean)

            chunks = self.chunker.chunk_text(section_clean, chunk_size=300)

            for chunk in chunks:
                chunk_str = chunk.strip()
                if not chunk_str:
                    continue

                metadata = {
                    "source": "market_research",
                    "category": category,
                    "company_name": company_name,
                    "industry": industry,
                    "agent": self.name,
                    "trigger_source": trigger_source,
                    "timestamp": now_iso,
                    # Research is useful context, but neither LLM output nor
                    # user-supplied text should silently become verified fact.
                    "content_origin": content_origin,
                    "generated_by": (
                        "bedrock" if content_origin == "llm_generated" else "user_input"
                    ),
                    "verified": False,
                    "confidence": "unverified",
                }
                structured_items.append({
                    "content": chunk_str,
                    "content_hash": create_content_hash(chunk_str),
                    "metadata": metadata,
                    "importance": 0.7,
                    "category": category,
                })

        return structured_items

    @staticmethod
    def _categorize_section(section: str) -> ResearchCategory:
        """Prefer the section heading and only then use keyword fallback."""

        heading = section.splitlines()[0].strip().lower()

        if heading.startswith(("competitor", "competitive landscape")):
            return "competitors"
        if heading.startswith(("industry trend", "market trend", "trend")):
            return "trends"
        if heading.startswith(("customer pain", "pain point", "unmet need")):
            return "pain_points"

        lower_text = section.lower()
        if "competitor" in lower_text:
            return "competitors"
        if any(
            keyword in lower_text
            for keyword in ("trend", "opportunity", "tailwind")
        ):
            return "trends"
        if any(
            keyword in lower_text
            for keyword in (
                "pain point",
                "unmet need",
                "friction",
                "customer",
            )
        ):
            return "pain_points"
        return "general"

    async def persist_memories(self, result_data: Any) -> List[Any]:
        """
        Dedup, embed via Bedrock, and persist memories via MemoryRepository.
        """
        if not isinstance(result_data, dict):
            return []

        structured_chunks = result_data.get("structured_chunks", [])
        if not structured_chunks:
            return []

        company_id = self.context.company_id
        pending_items = []
        pending_hashes = set()
        existing_ids = []

        # 3. Dedup Stage (Content Hash). This pre-check avoids needless
        # embeddings in the common case. The repository's UNIQUE constraint
        # and ON CONFLICT path remain the final concurrency-safe guarantee.
        for item in structured_chunks:
            content_hash = item["content_hash"]

            if content_hash in pending_hashes:
                continue

            existing_id = await self.context.memory_repository.get_by_content_hash(
                company_id, content_hash
            )
            if existing_id:
                existing_ids.append(existing_id)
                continue

            pending_hashes.add(content_hash)
            pending_items.append(item)

        if not pending_items:
            result_data["saved_memory_ids"] = existing_ids
            result_data["memories_created"] = 0
            result_data["memories_deduplicated"] = len(existing_ids)
            return existing_ids

        # 4. Embed Stage (Batched Bedrock Embedding Generation)
        texts = [item["content"] for item in pending_items]
        embeddings = await self.embedding_service.generate_embeddings(texts)

        if len(embeddings) != len(pending_items):
            raise ValueError(
                "Embedding service returned "
                f"{len(embeddings)} embeddings for "
                f"{len(pending_items)} pending items"
            )

        # Build MemoryInput list
        memory_inputs = []
        for item, embedding in zip(pending_items, embeddings):
            memory_inputs.append({
                "company_id": company_id,
                "memory_type": "semantic",
                "content": item["content"],
                "content_hash": item["content_hash"],
                "metadata": item["metadata"],
                "importance": item["importance"],
                "embedding": embedding,
            })

        # 5. Persist Stage (Batch persistence with ON CONFLICT & semantic dedup)
        new_ids = await self.context.memory_repository.save_memories_batch(memory_inputs)
        all_ids = list(existing_ids) + list(new_ids)

        result_data["saved_memory_ids"] = all_ids
        result_data["memories_created"] = len(new_ids)
        result_data["memories_deduplicated"] = len(existing_ids)

        return all_ids
