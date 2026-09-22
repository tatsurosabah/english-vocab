import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORDS_PATH = ROOT / "words_base.json"
DATA_PATH = ROOT / "data.js"
META_VERSION = 3
BOOK_WORDS = {
    "palm-fringed", "hawk", "more often than not", "collateral", "conjured",
    "wearing", "forensic", "magistrate", "foreword", "anomalies", "concisely",
    "unwavering", "instilled", "boundless", "supremacy", "bleak view", "glimmer",
    "conforms", "consociational", "contended", "communalism", "dictate", "tenure",
    "enshrined", "in retrospect", "in favour", "culminating", "materialised",
    "prudent", "imminent", "refine", "exacerbate", "entrenched", "stratification",
    "resentment", "veto",
}


words = json.loads(WORDS_PATH.read_text(encoding="utf-8"))
for word in words:
    if word.get("word", "").strip().lower() in BOOK_WORDS:
        word.update({
            "initialSetup": False,
            "addedAt": "2026-09-22",
            "source": "Citizenship in Crisis",
        })
    else:
        word.update({"initialSetup": True, "addedAt": None, "source": ""})
payload = json.dumps(words, ensure_ascii=False, separators=(",", ":"))
DATA_PATH.write_text(
    "// 英単語アプリ 初期データ（自動生成・編集しない）\n"
    f"const SEED_WORDS={payload};\n"
    f"const META_V={META_VERSION};\n",
    encoding="utf-8",
)
print(f"generated {DATA_PATH.name}: {len(words)} words, META_V={META_VERSION}")
