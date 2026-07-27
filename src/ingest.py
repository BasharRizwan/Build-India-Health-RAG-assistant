import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from .config import PIB_URL, SOURCE_TEXT


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag in {"p", "br", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        if tag in {"p", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            text = data.strip()
            if text:
                self.parts.append(text)


def fetch_html(url: str = PIB_URL) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "india-health-rag/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def html_to_text(html: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html)
    text = "\n".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    start = text.find("India's Health Transformation")
    if start == -1:
        start = text.find("India’s Health Transformation")
    end = text.find("References")
    if start != -1:
        text = text[start:end if end != -1 else None]
    return text.replace("India’s", "India's").replace("—", "-").replace("–", "-").strip()


def ingest(url: str = PIB_URL, output_path: Path = SOURCE_TEXT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = html_to_text(fetch_html(url))
    output_path.write_text(text, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = ingest()
    print(f"Wrote cleaned PIB text to {path}")

