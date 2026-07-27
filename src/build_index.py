import json

from .chunker import build_chunks
from .config import EMBEDDINGS_PATH
from .embeddings import HashingEmbeddingModel


def main() -> None:
    chunks = build_chunks()
    model = HashingEmbeddingModel()
    embeddings = model.embed_many(f"{chunk['title']}\n{chunk['text']}" for chunk in chunks)
    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_PATH.write_text(
        json.dumps(
            {
                "model": "local-hashing-embedding-v1",
                "dimensions": model.dimensions,
                "vectors": embeddings,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Indexed {len(chunks)} chunks in {EMBEDDINGS_PATH}")


if __name__ == "__main__":
    main()

