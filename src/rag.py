import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, List

from .config import CHUNKS_PATH, EMBEDDINGS_PATH
from .embeddings import HashingEmbeddingModel, cosine_similarity


SYSTEM_INSTRUCTION = (
    "You answer only from the provided PIB context. Keep the answer short, clear, "
    "and useful. If the context does not contain the answer, say that the PIB "
    "document does not provide enough information. Do not add outside facts."
)


@dataclass
class SearchHit:
    chunk: Dict[str, object]
    score: float


class RAGEngine:
    def __init__(self, chunks_path=CHUNKS_PATH, embeddings_path=EMBEDDINGS_PATH) -> None:
        self.chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        payload = json.loads(embeddings_path.read_text(encoding="utf-8"))
        self.vectors = payload["vectors"]
        self.embedding_model = HashingEmbeddingModel(dimensions=payload.get("dimensions", 768))

    def search(self, question: str, k: int = 4) -> List[SearchHit]:
        query_vector = self.embedding_model.embed(question)
        query_terms = self._terms(question)
        scored = [
            SearchHit(
                chunk=chunk,
                score=cosine_similarity(query_vector, vector) + self._metadata_boost(query_terms, chunk),
            )
            for chunk, vector in zip(self.chunks, self.vectors)
        ]
        scored.sort(key=lambda hit: hit.score, reverse=True)
        return scored[:k]

    def build_prompt(self, question: str, hits: List[SearchHit]) -> str:
        context_blocks = []
        for index, hit in enumerate(hits, start=1):
            chunk = hit.chunk
            context_blocks.append(
                f"[{index}] {chunk['title']} (score: {hit.score:.3f})\n{chunk['text']}"
            )
        return (
            f"{SYSTEM_INSTRUCTION}\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{chr(10).join(context_blocks)}\n\n"
            "Answer with 3-6 bullet points or a short paragraph. Cite chunk titles in plain text."
        )

    def answer(self, question: str, k: int = 4) -> Dict[str, object]:
        hits = self.search(question, k=k)
        prompt = self.build_prompt(question, hits)
        answer_text, mode = self._answer_with_openai(prompt)
        if not answer_text:
            answer_text, mode = self._extractive_answer(question, hits), "local-grounded"

        return {
            "question": question,
            "answer": answer_text,
            "mode": mode,
            "prompt": prompt,
            "sources": [
                {
                    "id": hit.chunk["id"],
                    "title": hit.chunk["title"],
                    "score": round(hit.score, 4),
                    "snippet": self._snippet(str(hit.chunk["text"]), question),
                    "source_url": hit.chunk["source_url"],
                }
                for hit in hits
            ],
        }

    def _answer_with_openai(self, prompt: str):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "", ""
        model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        payload = json.dumps(
            {
                "model": model,
                "input": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError):
            return "", ""
        if data.get("output_text"):
            return data["output_text"].strip(), f"openai:{model}"
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "").strip(), f"openai:{model}"
        return "", ""

    def _extractive_answer(self, question: str, hits: List[SearchHit]) -> str:
        question_terms = self._terms(question)
        candidates = []
        for hit in hits:
            sentences = re.split(r"(?<=[.!?])\s+", str(hit.chunk["text"]))
            for sentence in sentences:
                sentence_terms = self._terms(sentence)
                overlap = len(question_terms & sentence_terms)
                if overlap:
                    title_overlap = len(question_terms & self._terms(str(hit.chunk["title"])))
                    candidates.append((overlap + title_overlap, hit.score, hit.chunk["title"], sentence.strip()))
        if not candidates:
            return "The PIB document does not provide enough information to answer that question."
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        chosen = []
        seen = set()
        for _, _, title, sentence in candidates:
            key = sentence[:70]
            if key not in seen:
                chosen.append(f"- {sentence} ({title})")
                seen.add(key)
            if len(chosen) == 4:
                break
        return "\n".join(chosen)

    def _terms(self, text: str):
        return {
            term for term in re.findall(r"[a-z0-9-]+", text.lower()) if len(term) > 2
        }

    def _metadata_boost(self, query_terms, chunk: Dict[str, object]) -> float:
        title = str(chunk["title"]).lower()
        text = str(chunk["text"]).lower()
        title_hits = sum(1 for term in query_terms if term in title)
        phrase_hits = sum(1 for term in query_terms if term in text[:450])
        return (title_hits * 0.035) + (phrase_hits * 0.006)

    def _snippet(self, text: str, question: str) -> str:
        terms = [term for term in re.findall(r"[a-z0-9-]+", question.lower()) if len(term) > 3]
        lowered = text.lower()
        position = 0
        for term in terms:
            found = lowered.find(term)
            if found != -1:
                position = found
                break
        start = max(0, position - 110)
        end = min(len(text), position + 260)
        prefix = "..." if start else ""
        suffix = "..." if end < len(text) else ""
        return f"{prefix}{text[start:end].strip()}{suffix}"
