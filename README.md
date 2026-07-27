# India Health Lens

A small end-to-end RAG Q&A assistant for the PIB backgrounder **India's Health Transformation**.

It answers questions from one source only:
https://www.pib.gov.in/PressReleasePage.aspx?PRID=2269699&reg=48&lang=2

## What It Includes

- Document ingestion from the PIB page.
- Clean text conversion and titled chunking.
- Local vector embeddings for every chunk.
- Cosine-similarity semantic search over the chunk index.
- RAG prompt construction with retrieved evidence.
- Browser UI and CLI.
- Optional OpenAI answer generation when `OPENAI_API_KEY` is set.
- Local grounded fallback, so the demo works without paid API keys.

## Project Structure

```text
src/
  ingest.py       # downloads and cleans the PIB page
  chunker.py      # builds 200-500 word titled chunks where possible
  embeddings.py   # local hashing embedding model and cosine similarity
  build_index.py  # writes chunks.json and embeddings.json
  rag.py          # retrieval, prompt construction, answer generation
  server.py       # standard-library web server and API
  cli.py          # terminal interface
static/
  index.html
  app.css
  app.js
data/
  source/india_health_transformation.txt
  index/chunks.json
  index/embeddings.json
tests/
  test_rag.py
```

## Setup

Python 3.10+ is enough. No packages are required for the default demo.

```bash
python -m src.build_index
python -m src.server
```

Open:

```text
http://127.0.0.1:8000
```

CLI mode:

```bash
python -m src.cli
```

Run tests:

```bash
python -m unittest discover -s tests
```

## Optional LLM Mode

By default, the app uses local grounded sentence extraction after retrieval. That makes it reliable in an interview demo even without API keys.

For hosted LLM generation:

```bash
set OPENAI_API_KEY=your_key_here
set OPENAI_MODEL=gpt-4.1-mini
python -m src.server
```

The app still sends only retrieved PIB chunks to the model and asks it not to use outside facts.

## Ingestion and Chunking

`src/ingest.py` downloads the PIB HTML page with `urllib`, removes script/style content, extracts visible text, keeps the article body from the title through the section before references, and writes:

```text
data/source/india_health_transformation.txt
```

`src/chunker.py` reads this text, detects section headings, and merges nearby short sections into meaningful chunks. The chunk titles preserve the content area, such as AB-PMJAY, Ayushman Arogya Mandirs, PM-ABHIM, ABDM, NHM, communicable diseases, NCD screening, affordable medicines, and digital health.

The current seeded data is already cleaned from the same PIB page so the app can be run immediately.

## Embedding Storage

The index is stored as JSON:

```text
data/index/chunks.json
data/index/embeddings.json
```

`chunks.json` stores chunk id, title, text, word count, and source URL.

`embeddings.json` stores the embedding model name, vector dimensions, and one normalized vector per chunk. The default model is `local-hashing-embedding-v1`, a deterministic 768-dimensional local embedding method using token, phrase, acronym, and numeric features. It avoids downloads and keeps the repo portable.

## Semantic Search + RAG Flow

1. The user enters a question.
2. The question is embedded with the same embedding model used for chunks.
3. Cosine similarity ranks all chunks.
4. The top-k chunks are inserted into a grounded RAG prompt.
5. If an OpenAI key is present, the prompt is sent to the configured LLM.
6. Otherwise, the app returns a grounded extractive answer from the retrieved chunks.
7. The UI shows the answer, retrieval mode, cosine scores, and the evidence snippets.

## Demo Questions

- How does AB-PMJAY reduce healthcare costs for poor families?
- What services do Ayushman Arogya Mandirs provide?
- What is ABDM and how does ABHA work?
- What progress does the document mention on NCD screening?
- How did India expand telemedicine and last-mile care?

