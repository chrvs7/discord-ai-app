import os
import sys
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted

SYSTEM_PROMPT = (
    "You are a Discord bot. You are blunt, a little sarcastic, and mildly condescending — "
    "but you always actually answer the question and get the information across clearly. "
    "Think of yourself as the smartest person in the room who is slightly annoyed they have "
    "to explain things but does it anyway. Keep responses concise. Use Discord markdown "
    "formatting (bold, code blocks, bullet points) where it helps readability. Never be "
    "so rude that the response becomes useless — the snark is flavor, not the point."
)

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

conversation_histories: dict[int, list] = {}


async def get_response(user_id: int, prompt: str) -> str:
    """Send a prompt to Gemini with the user's conversation history and return the reply.

    Prepends the system prompt on every call, caps history at 20 entries,
    appends Google Search grounding sources to the response when available,
    and handles rate-limit errors gracefully.
    """
    history = conversation_histories.setdefault(user_id, [])
    history.append({"role": "user", "parts": [prompt]})

    # Keep only the last 20 messages
    if len(history) > 20:
        history[:] = history[-20:]

    full_history = [
        {"role": "user", "parts": [SYSTEM_PROMPT]},
        {"role": "model", "parts": ["Understood. I'll keep that personality in mind."]},
        *history,
    ]

    try:
        response = await model.generate_content_async(
            full_history,
            tools=[{"google_search": {}}],
        )
    except ResourceExhausted:
        return "Rate limit reached. Try again in a minute."
    except Exception:
        print("Error calling Gemini API", file=sys.stderr)
        raise

    text = response.text.strip() if response.text else ""

    if not text:
        return "No response was generated."

    # Append grounding sources if present
    try:
        metadata = response.candidates[0].grounding_metadata
        if metadata:
            urls = []
            for chunk in getattr(metadata, "grounding_chunks", []):
                url = getattr(getattr(chunk, "web", None), "uri", None)
                if url:
                    urls.append(url)
            if urls:
                sources = "\n".join(f"- {u}" for u in urls)
                text += f"\n\n**Sources:**\n{sources}"
    except (IndexError, AttributeError):
        pass

    history.append({"role": "model", "parts": [text]})
    return text


def clear_history(user_id: int) -> None:
    """Wipe the conversation history for the given Discord user ID."""
    conversation_histories.pop(user_id, None)
