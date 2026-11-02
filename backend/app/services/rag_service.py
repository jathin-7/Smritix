from __future__ import annotations
import re
import uuid
import json
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationMessage
from app.models.memory import Memory
from app.repositories.conversation_repository import ConversationRepository
from app.services.search_service import SearchService
from app.ai.registry import get_llm_provider
from app.schemas.ask import (
    AskResponse,
    SourceAttributionItem,
    ConversationItemResponse,
    ConversationDetailResponse,
    ConversationMessageResponse
)

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves", "tell", "please"
}

QUESTION_PREFIX_REGEX = re.compile(
    r"^(can you please |please |can you |could you |tell me |what is |what are |who is |who are |where is |where are |how do i |how can i |do you know |what did i save about |what do i know about )+",
    re.IGNORECASE
)

class RAGService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_service = SearchService(session)
        self.conversation_repo = ConversationRepository(session)

    def enhance_query(self, query: str) -> tuple[str, list[str], str]:
        """
        Step 1: Query Enhancement
        - Strips conversational boilerplate
        - Extracts prominent keywords for hybrid search
        - Detects user intent (summary, comparative, factual)
        """
        cleaned = QUESTION_PREFIX_REGEX.sub("", query.strip()).strip()
        if not cleaned:
            cleaned = query.strip()

        words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", cleaned.lower())
        keywords = [w for w in words if w not in STOP_WORDS]

        lower = query.lower()
        if any(term in lower for term in ["summarize", "summary", "overview", "recap", "brief"]):
            intent = "summary"
        elif any(term in lower for term in ["compare", "difference", "versus", "vs"]):
            intent = "comparative"
        else:
            intent = "factual"

        return cleaned, keywords, intent

    async def retrieve_and_assemble_context(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 5
    ) -> tuple[str, list[SourceAttributionItem]]:
        """
        Steps 2, 3, 4: Hybrid Retrieval, Reranking, and Context Assembly
        """
        cleaned_query, keywords, _ = self.enhance_query(query)

        # Primary hybrid search
        results = await self.search_service.hybrid_search(
            user_id=user_id,
            query=query,
            limit=limit,
            min_score=0.01
        )

        # Query expansion if results are sparse
        if len(results) < limit and cleaned_query != query:
            extra_results = await self.search_service.hybrid_search(
                user_id=user_id,
                query=cleaned_query,
                limit=limit,
                min_score=0.01
            )
            existing_ids = {r.memory_id for r in results}
            for extra in extra_results:
                if extra.memory_id not in existing_ids:
                    results.append(extra)
                    existing_ids.add(extra.memory_id)

        # Sort and take top N memories
        results.sort(key=lambda x: x.score, reverse=True)
        results = results[:limit]

        # Retrieve relevant indexed file chunks
        file_results = []
        try:
            file_results = await self.search_service.search_files(
                user_id=user_id,
                query=query,
                limit=limit,
                min_score=0.01
            )
        except Exception:
            file_results = []

        if not results and not file_results:
            context_str = "No relevant personal memories or indexed workspace documents were found in your knowledge base."
            return context_str, []

        source_items: list[SourceAttributionItem] = []
        context_blocks: list[str] = []
        current_idx = 1

        # 1. Add Memory Sources
        for item in results:
            source_item = SourceAttributionItem(
                index=current_idx,
                memory_id=item.memory_id,
                title=item.title or f"Memory #{str(item.memory_id)[:8]}",
                snippet=item.snippet,
                relevance_score=item.score,
                memory_type=item.memory_type,
                is_cited=False,
                source_category="memory"
            )
            source_items.append(source_item)
            block = f"[{current_idx}] Memory: {source_item.title}\nContent: {item.snippet}"
            context_blocks.append(block)
            current_idx += 1

        # 2. Add File Document Sources
        for f_item in file_results:
            page_info = f" (Page {f_item.page_number})" if f_item.page_number else (f" ({f_item.section_heading})" if f_item.section_heading else "")
            f_title = f"{f_item.file_name}{page_info}"
            source_item = SourceAttributionItem(
                index=current_idx,
                memory_id=f_item.file_id,
                title=f_title,
                snippet=f_item.snippet,
                relevance_score=f_item.score,
                memory_type="file",
                is_cited=False,
                source_category="file",
                file_id=f_item.file_id,
                file_path=f_item.absolute_path,
                page_number=f_item.page_number,
                section_heading=f_item.section_heading
            )
            source_items.append(source_item)
            block = f"[{current_idx}] Document File: {f_title} [Path: {f_item.relative_path}]\nContent: {f_item.snippet}"
            context_blocks.append(block)
            current_idx += 1

        context_str = "\n\n".join(context_blocks)
        return context_str, source_items

    def build_prompts(
        self,
        context_str: str,
        query: str,
        previous_messages: list[ConversationMessage] | None = None
    ) -> tuple[str, str]:
        """
        Builds system and user prompts with conversation history and context window.
        """
        system_prompt = (
            "You are SMRITIX, an intelligent personal memory and document assistant. "
            "Your purpose is to answer the user's questions truthfully and accurately using ONLY the personal memory and document context provided below.\n\n"
            "Guidelines:\n"
            "1. Answer concisely and cite your sources using bracket notation like [1], [2] when referencing facts.\n"
            "2. When citing files or documents, reference the document title and page or section if available.\n"
            "3. If the context does not contain enough information to answer, state clearly what you found in the memories/documents and explain what is missing.\n"
            "4. Do not invent facts, memories, or links that are not in the context."
        )

        history_text = ""
        if previous_messages:
            # Include last 4 messages for dialogue continuity
            recent = previous_messages[-4:]
            turns: list[str] = []
            for msg in recent:
                speaker = "User" if msg.role == "user" else "Assistant"
                turns.append(f"{speaker}: {msg.content}")
            if turns:
                history_text = "Previous conversation:\n" + "\n".join(turns) + "\n\n"

        user_prompt = (
            f"{history_text}"
            f"Context:\n{context_str}\n\n"
            f"Question: {query}"
        )

        return system_prompt, user_prompt

    def parse_citations(self, answer: str, sources: list[SourceAttributionItem]) -> list[SourceAttributionItem]:
        """
        Detects citation brackets [1], [2] in answer and updates is_cited flag.
        """
        cited_indices = set(re.findall(r"\[(\d+)\]", answer))
        for s in sources:
            if str(s.index) in cited_indices:
                s.is_cited = True
        return sources

    async def ask(
        self,
        user_id: uuid.UUID,
        query: str,
        conversation_id: uuid.UUID | None = None,
        limit: int = 5
    ) -> AskResponse:
        """
        Complete non-streaming RAG query execution.
        """
        conv = None
        previous_messages: list[ConversationMessage] = []
        if conversation_id:
            conv = await self.conversation_repo.get_conversation(conversation_id, user_id)
            if conv:
                previous_messages = await self.conversation_repo.get_conversation_messages(conv.id)

        if not conv:
            title = query.strip()[:40] + ("..." if len(query.strip()) > 40 else "")
            conv = await self.conversation_repo.create_conversation(user_id=user_id, title=title)

        # Record user message
        await self.conversation_repo.add_message(conv.id, role="user", content=query)

        # Retrieve and assemble context
        context_str, sources = await self.retrieve_and_assemble_context(user_id, query, limit=limit)

        system_prompt, user_prompt = self.build_prompts(
            context_str=context_str,
            query=query,
            previous_messages=previous_messages
        )

        llm = await get_llm_provider()
        completion = await llm.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=800
        )
        answer = completion.content

        sources = self.parse_citations(answer, sources)
        source_ids = [str(s.memory_id) for s in sources]

        # Record assistant message
        await self.conversation_repo.add_message(
            conv.id,
            role="assistant",
            content=answer,
            source_memories=source_ids
        )
        await self.session.commit()

        return AskResponse(
            conversation_id=conv.id,
            answer=answer,
            sources=sources
        )

    async def ask_stream(
        self,
        user_id: uuid.UUID,
        query: str,
        conversation_id: uuid.UUID | None = None,
        limit: int = 5
    ) -> AsyncIterator[str]:
        """
        Streaming RAG response via Server-Sent Events (SSE).
        Yields JSON-formatted event frames.
        """
        conv = None
        previous_messages: list[ConversationMessage] = []
        if conversation_id:
            conv = await self.conversation_repo.get_conversation(conversation_id, user_id)
            if conv:
                previous_messages = await self.conversation_repo.get_conversation_messages(conv.id)

        if not conv:
            title = query.strip()[:40] + ("..." if len(query.strip()) > 40 else "")
            conv = await self.conversation_repo.create_conversation(user_id=user_id, title=title)

        await self.conversation_repo.add_message(conv.id, role="user", content=query)

        context_str, sources = await self.retrieve_and_assemble_context(user_id, query, limit=limit)

        system_prompt, user_prompt = self.build_prompts(
            context_str=context_str,
            query=query,
            previous_messages=previous_messages
        )

        # 1. Send metadata event with sources and conversation_id
        meta_payload = {
            "type": "metadata",
            "conversation_id": str(conv.id),
            "sources": [s.model_dump(mode="json") for s in sources]
        }
        yield f"data: {json.dumps(meta_payload)}\n\n"

        llm = await get_llm_provider()
        accumulated_chunks: list[str] = []

        try:
            async for token in llm.stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=800
            ):
                accumulated_chunks.append(token)
                token_payload = {"type": "token", "token": token}
                yield f"data: {json.dumps(token_payload)}\n\n"
        except Exception as e:
            err_payload = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(err_payload)}\n\n"

        full_answer = "".join(accumulated_chunks)
        sources = self.parse_citations(full_answer, sources)
        source_ids = [str(s.memory_id) for s in sources]

        # Persist assistant message in DB
        await self.conversation_repo.add_message(
            conv.id,
            role="assistant",
            content=full_answer,
            source_memories=source_ids
        )
        await self.session.commit()

        # Send completion event
        done_payload = {
            "type": "done",
            "conversation_id": str(conv.id),
            "sources": [s.model_dump(mode="json") for s in sources]
        }
        yield f"data: {json.dumps(done_payload)}\n\n"

    async def list_conversations(self, user_id: uuid.UUID) -> list[ConversationItemResponse]:
        from sqlalchemy import func
        stmt = (
            select(
                Conversation.id,
                Conversation.title,
                Conversation.created_at,
                Conversation.updated_at,
                func.count(ConversationMessage.id).label("message_count")
            )
            .outerjoin(ConversationMessage, Conversation.id == ConversationMessage.conversation_id)
            .where(Conversation.user_id == user_id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
        )
        res = await self.session.execute(stmt)
        rows = res.all()
        return [
            ConversationItemResponse(
                id=row[0],
                title=row[1],
                created_at=row[2],
                updated_at=row[3],
                message_count=row[4]
            )
            for row in rows
        ]

    async def get_conversation_detail(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationDetailResponse | None:
        conv = await self.conversation_repo.get_conversation(conversation_id, user_id)
        if not conv:
            return None

        messages = await self.conversation_repo.get_conversation_messages(conversation_id)

        # Resolve referenced source memories
        all_referenced_ids: set[uuid.UUID] = set()
        for msg in messages:
            if msg.source_memories:
                for sm in msg.source_memories:
                    try:
                        all_referenced_ids.add(uuid.UUID(str(sm)))
                    except Exception:
                        pass

        memories_map: dict[uuid.UUID, Memory] = {}
        if all_referenced_ids:
            stmt = select(Memory).where(Memory.id.in_(all_referenced_ids))
            res = await self.session.execute(stmt)
            for m in res.scalars().all():
                memories_map[m.id] = m

        message_items: list[ConversationMessageResponse] = []
        for msg in messages:
            sources: list[SourceAttributionItem] = []
            if msg.source_memories:
                for idx, sm in enumerate(msg.source_memories, start=1):
                    try:
                        m_uuid = uuid.UUID(str(sm))
                        mem = memories_map.get(m_uuid)
                        if mem:
                            sources.append(
                                SourceAttributionItem(
                                    index=idx,
                                    memory_id=mem.id,
                                    title=mem.title,
                                    snippet=mem.content[:300],
                                    relevance_score=1.0,
                                    memory_type=mem.memory_type,
                                    is_cited=True
                                )
                            )
                    except Exception:
                        pass

            message_items.append(
                ConversationMessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    sources=sources,
                    created_at=msg.created_at
                )
            )

        return ConversationDetailResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=message_items
        )

    async def delete_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        deleted = await self.conversation_repo.delete_conversation(conversation_id, user_id)
        if deleted:
            await self.session.commit()
        return deleted
