from .rag import RAGEngine


def main() -> None:
    engine = RAGEngine()
    print("India Health RAG Assistant. Press Enter on an empty line to exit.")
    while True:
        question = input("\nQuestion: ").strip()
        if not question:
            break
        result = engine.answer(question)
        print("\nAnswer:")
        print(result["answer"])
        print("\nSources:")
        for source in result["sources"]:
            print(f"- {source['title']} | score {source['score']}")


if __name__ == "__main__":
    main()

