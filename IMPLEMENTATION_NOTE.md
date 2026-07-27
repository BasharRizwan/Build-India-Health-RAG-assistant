# Implementation Note

## Design Choices

This project was built as a small, reviewable RAG system rather than a heavy framework demo. The assignment values a clear pipeline, correct retrieval, and clean documentation, so the implementation uses Python standard library modules wherever possible. The browser app is served by `http.server`, the source page is ingested with `urllib`, and the index is stored as JSON files.

The interface is intentionally compact: question input on the left, answer below it, and evidence on the right. The reviewer can immediately see whether the answer is grounded because every response shows the retrieved chunk titles, snippets, and cosine scores. The UI avoids a generic chatbot look and instead feels like a focused evidence lens for one policy document.

## Embedding Model

The default embedding model is `local-hashing-embedding-v1`. It is a deterministic 768-dimensional local embedding method using token, phrase, acronym, and numeric features with L2 normalization. This was chosen for three reasons:

1. It works without downloading a model.
2. It handles assignment terms such as AB-PMJAY, PM-ABHIM, ABDM, ABHA, AAM, NHM, U-WIN, and eSanjeevani reliably.
3. It keeps the project simple enough to inspect in one sitting.

For a production version, I would replace the local model with a transformer embedding model or hosted embeddings, but the rest of the code would remain the same because retrieval only expects an `embed()` method.

## Storage and Index

Embeddings are stored in `data/index/embeddings.json`, and chunk metadata is stored in `data/index/chunks.json`. JSON was selected instead of a vector database because the assignment has one document and a small number of chunks. A vector database would add operational complexity without improving the core demonstration.

The chunker detects headings, preserves section meaning, and merges smaller sections into chunks close to the requested 200-500 word range. The resulting chunks cover the major PIB sections: universal health coverage, AB-PMJAY, Ayushman Arogya Mandirs, PM-ABHIM, ABDM, NHM, immunisation, communicable diseases, COVID-19 response, NCD screening, affordable medicines, digital health, AI, medical education, AYUSH, and Viksit Bharat 2047.

## LLM and Prompt Design

The RAG prompt contains a strict system instruction, the user question, and only the top retrieved PIB chunks. The instruction tells the model to answer only from context and to say when the document does not provide enough information. This reduces hallucination risk.

The app has two answer paths:

- Hosted LLM path: enabled when `OPENAI_API_KEY` is set. The default model name is configurable through `OPENAI_MODEL`.
- Local grounded path: used when no API key is available. It selects high-overlap sentences from retrieved chunks and formats them with chunk titles.

This makes the project demo-safe: it can be shown offline, but it still contains a proper LLM prompt path for the assignment.

## What I Had To Learn or Research

I reviewed the PIB backgrounder structure and converted the document into section-level text suitable for retrieval. The key challenge was balancing chunk size with meaning: several PIB sections are short bullet-heavy policy updates, so the chunker merges related sections while preserving titles. I also checked the assignment PDF to make sure the deliverables were covered: ingestion, chunking, embeddings, search, RAG prompt, UI or CLI, README, and implementation note.

## Limitations

The local hashing embedding model is lightweight and dependable, but it is not as semantically rich as a transformer embedding model. It performs well on named programmes and policy terms, but it may miss vague paraphrases. The seeded text is a cleaned copy of the PIB article content; running `src.ingest` refreshes from the live PIB URL when internet access is available. The fallback answer mode is extractive, so it is safer but less fluent than a hosted LLM.

## Improvements With Two More Days

I would add a hosted embedding provider, streaming answer tokens, evaluation questions with expected citations, a small admin page showing chunk boundaries, and a deploy target such as Render or Railway. I would also add a one-click script that refreshes the PIB page, rebuilds the index, runs tests, and opens the app.

