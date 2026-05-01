from __future__ import annotations

EXTRACTION_PROMPT = (
    "You are a memory extraction system. "
    "Given a conversation text, extract distinct concepts, "
    "facts, or ideas that represent new knowledge worth remembering.\n"
    "\n"
    "EXISTING MEMORY NODES (do NOT extract duplicates of these):\n"
    "{existing_ids}\n"
    "\n"
    "RULES:\n"
    "1. Extract only concepts NOT already in existing memory\n"
    "2. Ignore conversational filler (greetings, acknowledgments, small talk)\n"
    "3. Each extracted item should be a single, atomic concept\n"
    "4. Return valid JSON only - no explanation text\n"
    "\n"
    "Return a JSON array where each item has:\n"
    '- "content": a clear description of the concept (1-2 sentences)\n'
    '- "label": a short human-readable title (2-4 words)\n'
    '- "connects_to": array of existing node IDs this relates to (can be empty)\n'
    "\n"
    "CONVERSATION TEXT:\n"
    "{text}\n"
    "\n"
    "RESPONSE (JSON array only):"
)

DEDUPLICATION_CHECK = (
    "Given the following new concept and existing memory nodes, "
    "determine if this concept is already captured by any existing node.\n"
    "\n"
    "NEW CONCEPT: {new_content}\n"
    "\n"
    "EXISTING NODES:\n"
    "{existing_nodes}\n"
    "\n"
    'If already captured, respond with the existing node ID. '
    'If new, respond with "NEW".\n'
    "\n"
    "RESPONSE:"
)
