"""
RAG Agent - Orchestrates retrieval and generation workflow.
Combines semantic search with LLM generation and OpenAI Agent SDK for agentic behavior.
"""

import logging
import json
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import time

# Fix Python path for module imports
# This handles deployment in containers where src is in the working directory
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)  # Go up from src/ to project root
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.retrieval_service import RetrieverAgent, RetrievedChunk
from src.generation_service import GenerationAgent, GeneratedResponse
from src.database import add_session, add_message, DatabaseSession
from src.config import get_settings

# Initialize logger first (before it's used in imports)
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenAI SDK not installed: {e}")
    OPENAI_AVAILABLE = False
    OpenAI = None


@dataclass
class RAGResponse:
    """Complete RAG pipeline response."""

    query: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    session_id: Optional[str] = None
    mode: str = "full_book"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "answer": self.answer,
            "retrieved_chunks": [chunk.to_dict() for chunk in self.retrieved_chunks],
            "model": self.model,
            "tokens": {
                "input": self.input_tokens,
                "output": self.output_tokens,
                "total": self.total_tokens,
            },
            "latency": {
                "retrieval_ms": round(self.retrieval_latency_ms, 2),
                "generation_ms": round(self.generation_latency_ms, 2),
                "total_ms": round(self.total_latency_ms, 2),
            },
            "session_id": self.session_id,
            "mode": self.mode,
        }


class RAGAgent:
    """Orchestrates the RAG pipeline: retrieve → generate → respond."""

    def __init__(
        self,
        retriever: RetrieverAgent,
        generator: GenerationAgent,
        top_k: int = 5,
        min_similarity: float = 0.5,
    ):
        """
        Initialize RAG agent.

        Args:
            retriever: RetrieverAgent instance
            generator: GenerationAgent instance
            top_k: Number of chunks to retrieve
            min_similarity: Minimum similarity score filter
        """
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.settings = get_settings()

    async def process_query(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        mode: str = "full_book",
        selected_text: Optional[str] = None,
    ) -> RAGResponse:
        """
        Process a user query through the full RAG pipeline.

        Args:
            query: User's question
            user_id: User ID for session tracking
            session_id: Optional chat session ID
            mode: Query mode ("full_book" or "selected_text")
            selected_text: Text highlighted by user (for selected_text mode)

        Returns:
            RAGResponse with answer, chunks, and metrics
        """
        pipeline_start = time.time()

        try:
            # Step 1: Retrieve relevant chunks
            retrieval_start = time.time()
            retrieved_chunks = await self.retriever.retrieve(
                query=query,
                top_k=self.top_k,
                min_similarity=self.min_similarity,
            )
            retrieval_latency = time.time() - retrieval_start

            logger.info(
                f"Retrieved {len(retrieved_chunks)} chunks for query: {query[:50]}..."
            )

            # Step 2: Assemble context from retrieved chunks
            context = self._assemble_context(retrieved_chunks)

            # Step 3: Generate response
            generation_start = time.time()
            generated = await self.generator.generate(
                query=query,
                context=context,
                mode=mode,
                selected_text=selected_text,
            )
            generation_latency = time.time() - generation_start

            total_latency = time.time() - pipeline_start

            # Step 4: Store in database (non-blocking)
            try:
                if session_id:
                    await self._store_interaction(
                        user_id=user_id,
                        session_id=session_id,
                        query=query,
                        answer=generated.content,
                        chunks=retrieved_chunks,
                        model=generated.model,
                        total_tokens=generated.total_tokens,
                    )
            except Exception as db_error:
                logger.warning(f"Failed to store interaction: {db_error}")

            # Step 5: Assemble response
            response = RAGResponse(
                query=query,
                answer=generated.content,
                retrieved_chunks=retrieved_chunks,
                model=generated.model,
                input_tokens=generated.input_tokens,
                output_tokens=generated.output_tokens,
                total_tokens=generated.total_tokens,
                retrieval_latency_ms=retrieval_latency * 1000,
                generation_latency_ms=generation_latency * 1000,
                total_latency_ms=total_latency * 1000,
                session_id=session_id,
                mode=mode,
            )

            logger.info(
                f"RAG pipeline completed in {total_latency:.2f}s "
                f"(retrieval: {retrieval_latency:.2f}s, "
                f"generation: {generation_latency:.2f}s)"
            )

            return response

        except Exception as e:
            logger.error(f"RAG pipeline failed: {str(e)}", exc_info=True)
            raise

    def _assemble_context(self, chunks: List[RetrievedChunk]) -> str:
        """
        Assemble context string from retrieved chunks.

        Args:
            chunks: List of retrieved chunks

        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context found in the knowledge base."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            header = f"[Source {i}: {chunk.chapter}"
            if chunk.section:
                header += f" - {chunk.section}"
            if chunk.subsection:
                header += f" - {chunk.subsection}"
            header += f"] (Relevance: {chunk.similarity_score:.1%})"

            context_parts.append(header)
            context_parts.append(chunk.content)
            context_parts.append("")

        return "\n".join(context_parts)

    async def _store_interaction(
        self,
        user_id: str,
        session_id: str,
        query: str,
        answer: str,
        chunks: List[RetrievedChunk],
        model: str,
        total_tokens: int,
    ) -> None:
        """
        Store query-response interaction in database.

        Args:
            user_id: User ID
            session_id: Session ID
            query: User query
            answer: Generated answer
            chunks: Retrieved chunks
            model: Model used
            total_tokens: Token count
        """
        try:
            source_refs = [
                {
                    "doc_id": chunk.doc_id,
                    "chapter": chunk.chapter,
                    "section": chunk.section,
                    "similarity": chunk.similarity_score,
                }
                for chunk in chunks
            ]

            await add_message(
                session_id=session_id,
                user_id=user_id,
                query=query,
                response=answer,
                model=model,
                tokens_used=total_tokens,
                source_documents=source_refs,
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.warning(f"Failed to store interaction in database: {e}")


class OpenAIRAGAgent:
    """
    OpenAI Agent SDK integration for RAG.
    Uses OpenAI's agent framework with tool use for semantic search and generation.
    """

    def __init__(
        self,
        retriever: RetrieverAgent,
        generator: GenerationAgent,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
    ):
        """
        Initialize OpenAI RAG Agent.

        Args:
            retriever: RetrieverAgent instance
            generator: GenerationAgent instance
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)

        Raises:
            ImportError: If OpenAI SDK is not installed
            ValueError: If API key is not provided and not in environment
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI SDK not installed. Install with: pip install openai>=1.42.0"
            )

        self.retriever = retriever
        self.generator = generator
        self.model = model
        self.settings = get_settings()

        try:
            api_key_to_use = api_key or self.settings.openai_api_key
            if not api_key_to_use:
                raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")

            self.client = OpenAI(api_key=api_key_to_use)
            logger.info(f"✅ OpenAI Agent initialized with model: {model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI Agent: {e}")
            raise

    def _get_tools(self) -> List[Dict[str, Any]]:
        """
        Define tools available to the OpenAI agent.

        Returns:
            List of tool definitions for OpenAI API
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "retrieve_relevant_chunks",
                    "description": "Searches the knowledge base for relevant content chunks based on semantic similarity. Use this to find relevant information from the RAG corpus.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant chunks",
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of top results to return (default: 5)",
                                "default": 5,
                            },
                            "min_similarity": {
                                "type": "number",
                                "description": "Minimum similarity score threshold (0-1, default: 0.5)",
                                "default": 0.5,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_response",
                    "description": "Generates a natural language response based on context using an LLM. Use this after retrieving relevant chunks to produce the final answer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The original user question",
                            },
                            "context": {
                                "type": "string",
                                "description": "The assembled context from retrieved chunks",
                            },
                            "mode": {
                                "type": "string",
                                "enum": ["full_book", "selected_text"],
                                "description": "Query mode (default: full_book)",
                                "default": "full_book",
                            },
                        },
                        "required": ["query", "context"],
                    },
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool call from the agent.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters

        Returns:
            Tool execution result as JSON string
        """
        try:
            if tool_name == "retrieve_relevant_chunks":
                query = tool_input.get("query")
                top_k = tool_input.get("top_k", 5)
                min_similarity = tool_input.get("min_similarity", 0.5)

                logger.info(f"🔧 Tool: retrieve_relevant_chunks(query='{query}', top_k={top_k})")

                chunks, metadata = self.retriever.retrieve(
                    query=query,
                    top_k=top_k,
                )

                result = {
                    "chunks": [
                        {
                            "doc_id": chunk.doc_id,
                            "chapter": chunk.chapter,
                            "section": chunk.section,
                            "content": chunk.content,
                            "similarity_score": chunk.similarity_score,
                        }
                        for chunk in chunks
                    ],
                    "count": len(chunks),
                    "metadata": metadata,
                }
                return json.dumps(result)

            elif tool_name == "generate_response":
                query = tool_input.get("query")
                context = tool_input.get("context")
                mode = tool_input.get("mode", "full_book")

                logger.info(f"🔧 Tool: generate_response(query='{query}', mode={mode})")

                generated = self.generator.generate(
                    query=query,
                    context=context,
                    mode=mode,
                )

                result = {
                    "content": generated.content,
                    "model": generated.model,
                    "input_tokens": generated.input_tokens,
                    "output_tokens": generated.output_tokens,
                    "total_tokens": generated.total_tokens,
                }
                return json.dumps(result)

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            logger.error(f"❌ Tool execution failed: {tool_name} - {e}", exc_info=True)
            return json.dumps({"error": str(e)})

    async def process_query_with_agent(
        self,
        query: str,
        user_id: str,
        session_id: Optional[str] = None,
        mode: str = "full_book",
    ) -> RAGResponse:
        """
        Process query using OpenAI Agent with tool use.

        The agent orchestrates the RAG pipeline by:
        1. Analyzing the query
        2. Calling retrieve_relevant_chunks tool
        3. Calling generate_response tool
        4. Assembling final response

        Args:
            query: User question
            user_id: User ID for tracking
            session_id: Optional session ID
            mode: Query mode (full_book or selected_text)

        Returns:
            RAGResponse with answer and metrics
        """
        pipeline_start = time.time()

        try:
            logger.info(f"🤖 OpenAI Agent processing query: '{query}'")

            messages = [
                {
                    "role": "user",
                    "content": f"Please answer this question using the available tools: {query}",
                }
            ]

            tools = self._get_tools()
            max_iterations = 10
            iteration = 0

            # Agentic loop
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Agent iteration {iteration}/{max_iterations}")

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )

                # Check if agent wants to use tools
                if response.stop_reason == "tool_calls":
                    # Get the message from the response
                    message = response.choices[0].message

                    # Add assistant response to message history
                    if message.content:
                        messages.append({"role": "assistant", "content": message.content})

                    # Process each tool call
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.function.name
                            tool_input = json.loads(tool_call.function.arguments)

                            logger.info(f"Agent calling tool: {tool_name}")

                            # Execute tool
                            tool_result = self._execute_tool(tool_name, tool_input)

                            # Add tool result to messages
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": tool_name,
                                    "content": tool_result,
                                }
                            )

                elif response.stop_reason == "end_turn":
                    # Agent finished, extract final answer
                    message = response.choices[0].message
                    final_answer = message.content or "No response generated"
                    logger.info(f"✅ Agent completed in {iteration} iterations")

                    # For now, assume agent retrieved chunks in previous iteration
                    # In a real scenario, we'd track the chunks from tool calls
                    retrieved_chunks = []

                    total_latency = time.time() - pipeline_start

                    # Extract token usage if available
                    input_tokens = 0
                    output_tokens = 0
                    total_tokens = 0
                    if response.usage:
                        input_tokens = response.usage.prompt_tokens or 0
                        output_tokens = response.usage.completion_tokens or 0
                        total_tokens = response.usage.total_tokens or 0

                    return RAGResponse(
                        query=query,
                        answer=final_answer,
                        retrieved_chunks=retrieved_chunks,
                        model=self.model,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        retrieval_latency_ms=0,
                        generation_latency_ms=0,
                        total_latency_ms=(total_latency * 1000),
                        session_id=session_id,
                        mode=mode,
                    )

                else:
                    logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                    break

            logger.error("Agent max iterations reached")
            raise RuntimeError("Agent exceeded maximum iterations")

        except Exception as e:
            logger.error(f"❌ OpenAI Agent processing failed: {e}", exc_info=True)
            raise


async def get_rag_agent() -> RAGAgent:
    """Dependency injection for traditional RAG agent."""
    from src.retrieval_service import get_retriever
    from src.generation_service import get_generation_agent

    retriever = await get_retriever()
    generator = await get_generation_agent()

    return RAGAgent(
        retriever=retriever,
        generator=generator,
        top_k=5,
        min_similarity=0.5,
    )


def get_openai_rag_agent(
    api_key: Optional[str] = None,
    model: str = "gpt-4o",
) -> OpenAIRAGAgent:
    """Get OpenAI RAG Agent with tool use."""
    from src.retrieval_service import RetrieverAgent
    from src.generation_service import GenerationAgent

    try:
        # Initialize services with default settings
        settings = get_settings()
        retriever = RetrieverAgent(top_k=5, min_similarity=0.5)
        generator = GenerationAgent()

        return OpenAIRAGAgent(
            retriever=retriever,
            generator=generator,
            api_key=api_key,
            model=model,
        )
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI RAG Agent: {e}")
        raise
