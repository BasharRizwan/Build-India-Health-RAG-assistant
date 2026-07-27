import unittest

from src.rag import RAGEngine


class RAGEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = RAGEngine()

    def test_retrieves_ab_pmjay(self):
        hits = self.engine.search("What does AB-PMJAY cover?", k=3)
        titles = " ".join(hit.chunk["title"] for hit in hits)
        self.assertIn("AB-PMJAY", titles)

    def test_answer_returns_sources(self):
        result = self.engine.answer("How does eSanjeevani help remote patients?")
        self.assertTrue(result["answer"])
        self.assertGreaterEqual(len(result["sources"]), 1)
        self.assertIn("prompt", result)

    def test_unknown_question_is_still_grounded(self):
        result = self.engine.answer("What does the document say about railway freight pricing?")
        self.assertTrue(result["answer"])
        self.assertEqual(result["mode"], "local-grounded")


if __name__ == "__main__":
    unittest.main()

