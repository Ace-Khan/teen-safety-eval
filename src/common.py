import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
GUIDE = ROOT / "guide" / "labeling_guide.md"

LABELS = ["self_harm", "grooming", "dangerous_challenge", "age_inappropriate", "misinformation", "safe"]
UNSAFE = LABELS[:-1]


def load_posts():
    with open(DATA / "posts.csv") as f:
        return list(csv.DictReader(f))


def guide_text():
    return GUIDE.read_text()


def rule_ids():
    # rule IDs look like **SH-1**, **P-2**, etc.
    return set(re.findall(r"\*\*([A-Z]{1,2}-\d)\*\*", guide_text()))


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]
