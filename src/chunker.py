import json
import re
from pathlib import Path
from typing import Dict, List

from .config import CHUNKS_PATH, PIB_URL, SOURCE_TEXT


HEADING_RE = re.compile(r"^[A-Z][A-Za-z0-9 ():/.'&-]{2,85}$")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w-]+\b", text))


def read_sections(path: Path = SOURCE_TEXT) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []
    current_title = "Overview"
    current_lines: List[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        looks_like_heading = bool(HEADING_RE.match(line)) and not line.endswith(".")
        if looks_like_heading:
            if current_lines:
                sections.append({"title": current_title, "text": " ".join(current_lines)})
            current_title = line
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({"title": current_title, "text": " ".join(current_lines)})
    return sections


def chunk_sections(sections: List[Dict[str, str]], min_words: int = 180, max_words: int = 500) -> List[Dict[str, object]]:
    chunks: List[Dict[str, object]] = []
    pending_title = ""
    pending_text: List[str] = []

    def flush() -> None:
        nonlocal pending_title, pending_text
        if not pending_text:
            return
        text = " ".join(pending_text).strip()
        chunks.append(
            {
                "id": f"chunk-{len(chunks) + 1:02d}",
                "title": pending_title,
                "text": text,
                "word_count": word_count(text),
                "source_url": PIB_URL,
            }
        )
        pending_title = ""
        pending_text = []

    for section in sections:
        title = section["title"]
        text = section["text"]
        count = word_count(" ".join(pending_text + [text]))
        if not pending_text:
            pending_title = title
            pending_text = [text]
        elif count <= max_words:
            pending_title = f"{pending_title} + {title}"
            pending_text.append(text)
        else:
            if word_count(" ".join(pending_text)) >= min_words:
                flush()
                pending_title = title
                pending_text = [text]
            else:
                pending_title = f"{pending_title} + {title}"
                pending_text.append(text)
                flush()

    flush()
    return chunks


def build_chunks(source_path: Path = SOURCE_TEXT, output_path: Path = CHUNKS_PATH) -> List[Dict[str, object]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = chunk_sections(read_sections(source_path))
    output_path.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    return chunks


if __name__ == "__main__":
    made = build_chunks()
    print(f"Wrote {len(made)} chunks to {CHUNKS_PATH}")
