CHUNK_LIMIT = 1900


def split_message(text: str) -> list[str]:
    """Split a message into Discord-safe chunks of at most 1900 characters.

    Avoids splitting inside triple-backtick code blocks. When a split must
    happen inside an open code fence, the fence is closed before the break
    and reopened (with the same language tag) at the start of the next chunk.
    Splits on newlines where possible rather than mid-word.
    """
    if len(text) <= CHUNK_LIMIT:
        return [text]

    chunks = []
    current_chunk = ""
    in_code_block = False
    current_lang = ""

    lines = text.split("\n")

    for line in lines:
        # Detect code fence toggles
        if line.startswith("```"):
            if not in_code_block:
                in_code_block = True
                current_lang = line[3:].strip()
            else:
                in_code_block = False
                current_lang = ""

        candidate = (current_chunk + "\n" + line) if current_chunk else line

        if len(candidate) <= CHUNK_LIMIT:
            current_chunk = candidate
        else:
            # Need to start a new chunk. Close open code block first.
            if in_code_block:
                chunks.append(current_chunk + "\n```")
                current_chunk = f"```{current_lang}\n{line}"
            else:
                chunks.append(current_chunk)
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
