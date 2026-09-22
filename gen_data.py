import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORDS_PATH = ROOT / "words_base.json"
DATA_PATH = ROOT / "data.js"
META_VERSION = 2


words = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
payload = json.dumps(words, ensure_ascii=False, separators=(",", ":"))
DATA_PATH.write_text(
    "// 英単語アプリ 初期データ（自動生成・編集しない）\n"
    f"const SEED_WORDS={payload};\n"
    f"const META_V={META_VERSION};\n",
    encoding="utf-8",
)
print(f"generated {DATA_PATH.name}: {len(words)} words, META_V={META_VERSION}")
