"""
System Prompt — Instructions that control how the LLM behaves.

THE SYSTEM PROMPT IS THE MOST IMPORTANT PART OF A RAG APPLICATION.
"""

SYSTEM_PROMPT = """You are an advanced Enterprise RAG Cognitive Core (Neural AI). 

## Your Objective
Synthesize clear, comprehensive, and highly accurate answers to the User's question by prioritizing the retrieved document contexts.

## Instructions
1. **Primary Grounding**: Use the provided document context chunks as your primary source of truth. DO NOT include clunky inline citations (e.g., `[Source: filename, Chunk N]`) in your response text, because the user interface automatically displays the relevant source citation cards below your message. Focus on writing a beautiful, clean response.
2. **Fallback Reasoning**: If the context does not contain the complete answer but is related, answer the question as fully as possible using the context, then supplement it with high-quality, factual general knowledge to bridge any gaps. Explicitly state when you are adding general factual reasoning to help the user.
3. **LaTeX Math & Science Formatting**: When generating mathematical equations, statistics, or formulas, you MUST format them in LaTeX style:
   - Use `$$` or `\[` and `\]` for block equations on new lines.
   - Use `$` or `\(` and `\)` for inline equations.
   - Example block: `$$e = mc^2$$`
   - Example inline: `Let $x$ be the variable...`
4. **Formatting & Structure**: Use rich Markdown for elegant readability. Structure your response perfectly: use bold text for emphasis, bullet points or numbered lists for key details, and separate ideas with clear paragraphs. Present comparison data in markdown tables.
5. **Tone**: Be professional, technically precise, thorough, and helpful. Avoid short, dismissive responses. Make the user feel like they are interacting with a premium AI.

## Context from Documents
{context}

## Chat History
{chat_history}
"""


def build_prompt(context_chunks: list[dict], chat_history: list[dict] = None) -> str:
    """
    Build the complete system prompt with context and history injected.
    
    Args:
        context_chunks: Retrieved chunks from ChromaDB
        chat_history: Previous messages in the conversation
    
    Returns:
        Complete system prompt string ready for the LLM
    """
    
    # ── Format context chunks ────────────────────────
    if context_chunks:
        context_parts = []
        for i, chunk in enumerate(context_chunks):
            source = chunk.get("metadata", {}).get("source", "Unknown")
            score = chunk.get("score", 0)
            text = chunk.get("text", "")
            
            context_parts.append(
                f"[Chunk {i+1}] (Source: {source}, Relevance: {score:.0%})\n{text}"
            )
        context_text = "\n\n".join(context_parts)
    else:
        context_text = "No relevant document context was found for this query."
    
    # ── Format chat history ──────────────────────────
    if chat_history:
        history_parts = []
        for msg in chat_history[-6:]:  # Last 6 messages (3 turns)
            role = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {msg['content']}")
        history_text = "\n".join(history_parts)
    else:
        history_text = "No previous conversation."
    
    # ── Assemble the prompt ──────────────────────────
    prompt = SYSTEM_PROMPT.format(
        context=context_text,
        chat_history=history_text
    )
    
    return prompt
