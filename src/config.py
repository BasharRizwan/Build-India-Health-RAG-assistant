from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
INDEX_DIR = DATA_DIR / "index"
STATIC_DIR = ROOT / "static"

PIB_URL = "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2269699&reg=48&lang=2"
SOURCE_TEXT = SOURCE_DIR / "india_health_transformation.txt"
CHUNKS_PATH = INDEX_DIR / "chunks.json"
EMBEDDINGS_PATH = INDEX_DIR / "embeddings.json"

