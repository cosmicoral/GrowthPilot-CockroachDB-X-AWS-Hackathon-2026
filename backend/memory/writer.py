from backend.memory.hash import create_content_hash


class MemoryWriter:
    """
    Coordinates the memory creation pipeline.

    Supports both:
    - the existing chunk-based memory writing interface
    - extraction-policy-based memory writing

    Chunk-based flow:

    Text
      ↓
    Chunker
      ↓
    Embedding Service
      ↓
    Repository
      ↓
    CockroachDB

    Extraction flow:

    Text
      ↓
    Memory Extraction Policy
      ↓
    Embedding Service
      ↓
    Repository
      ↓
    CockroachDB
    """

    def __init__(
        self,
        chunker,
        embedding_service,
        repository,
        extraction_policy=None,
    ):
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.repository = repository
        self.extraction_policy = extraction_policy

    async def write(
        self,
        company_id,
        text: str,
        memory_type: str = "semantic",
        metadata: dict | None = None,
        importance: float = 0.5,
    ):
        """
        Convert text into stored memories.

        When an extraction policy is configured, extracted memories are
        persisted. Otherwise, the existing chunk-based behavior is used.
        """

        if self.extraction_policy is not None:
            return await self._write_extracted(
                company_id=company_id,
                text=text,
            )

        return await self._write_chunks(
            company_id=company_id,
            text=text,
            memory_type=memory_type,
            metadata=metadata,
            importance=importance,
        )

    async def _write_extracted(
        self,
        company_id,
        text: str,
    ):
        extraction_result = await self.extraction_policy.extract(text)

        if not extraction_result.memories:
            return []

        pending_chunks = []
        pending_hashes = set()
        saved_memories = []

        for memory in extraction_result.memories:
            content_hash = create_content_hash(memory.content)

            if content_hash in pending_hashes:
                continue

            existing_memory_id = await (
                self.repository.get_by_content_hash(
                    company_id,
                    content_hash,
                )
            )

            if existing_memory_id:
                saved_memories.append(existing_memory_id)
                continue

            pending_hashes.add(content_hash)

            pending_chunks.append(
                {
                    "content": memory.content,
                    "content_hash": content_hash,
                    "memory_type": memory.memory_type,
                    "metadata": memory.metadata,
                    "importance": memory.importance,
                }
            )

        return await self._persist_pending(
            company_id=company_id,
            pending_chunks=pending_chunks,
            saved_memories=saved_memories,
        )

    async def _write_chunks(
        self,
        company_id,
        text: str,
        memory_type: str,
        metadata: dict | None,
        importance: float,
    ):
        chunks = self.chunker.chunk_text(text)

        pending_chunks = []
        pending_hashes = set()
        saved_memories = []

        for chunk in chunks:
            content_hash = create_content_hash(chunk)

            if content_hash in pending_hashes:
                continue

            existing_memory_id = await (
                self.repository.get_by_content_hash(
                    company_id,
                    content_hash,
                )
            )

            if existing_memory_id:
                saved_memories.append(existing_memory_id)
                continue

            pending_hashes.add(content_hash)

            pending_chunks.append(
                {
                    "content": chunk,
                    "content_hash": content_hash,
                    "memory_type": memory_type,
                    "metadata": metadata or {},
                    "importance": importance,
                }
            )

        return await self._persist_pending(
            company_id=company_id,
            pending_chunks=pending_chunks,
            saved_memories=saved_memories,
        )

    async def _persist_pending(
        self,
        company_id,
        pending_chunks,
        saved_memories,
    ):
        if not pending_chunks:
            return saved_memories

        texts = [
            item["content"]
            for item in pending_chunks
        ]

        embeddings = await self.embedding_service.generate_embeddings(
            texts
        )

        if len(embeddings) != len(pending_chunks):
            raise ValueError(
                "Embedding service returned a different number of "
                "embeddings than the number of pending chunks"
            )

        memories = []

        for item, embedding in zip(pending_chunks, embeddings):
            memories.append(
                {
                    "company_id": company_id,
                    "memory_type": item["memory_type"],
                    "content": item["content"],
                    "content_hash": item["content_hash"],
                    "metadata": item["metadata"],
                    "importance": item["importance"],
                    "embedding": embedding,
                }
            )

        ids = await self.repository.save_memories_batch(memories)

        saved_memories.extend(ids)

        return saved_memories