"""Can an LLM pre-label so humans only look at the hard ones?

Two routing rules, swept over confidence thresholds:
  conf  - auto-accept the model's label if confidence >= t, humans review the rest
  agree - auto-accept only when both models agree AND both are >= t

Reviewed items are assumed to end up correct (a human fixes them). We report how many
items still need a human, the accuracy of the final label set, and how many unsafe posts
slip through as auto-accepted "safe".

    python src/prelabel.py claude-opus-5-5 claude-haiku-5-5
"""
import argparse
import csv
from statistics import median

from common import DATA, UNSAFE, load_posts, preds_path, read_jsonl

DEFAULT_SECONDS = 15.0  # used until a timed human pass exists
THRESHOLDS = [0.5, 0.7, 0.8, 0.9, 0.95]


def seconds_per_item():
    path = DATA / "annotator_b.csv"
    if path.exists():
        secs = [float(r["seconds"]) for r in csv.DictReader(path.open())]
        if secs:
            return median(secs), "median of the timed human pass"
    return DEFAULT_SECONDS, "assumed"


def simulate(posts, accept):
    """accept(post_id) -> label to auto-accept, or None to send to a human."""
    reviewed, correct, leaked = 0, 0, 0
    for p in posts:
        lab = accept(p["id"])
        if lab is None:
            reviewed += 1
            correct += 1
        else:
            correct += lab == p["label"]
            leaked += p["label"] in UNSAFE and lab == "safe"
    return reviewed, correct / len(posts), leaked


def main(primary, second=None, data="posts"):
    posts = load_posts(data)
    a = {r["id"]: r for r in read_jsonl(preds_path(primary, data))}
    b = {r["id"]: r for r in read_jsonl(preds_path(second, data))} if second else {}
    posts = [p for p in posts if p["id"] in a and (not b or p["id"] in b)]
    n = len(posts)
    sec, src = seconds_per_item()

    def ok(r, t):
        return r["confidence"] is not None and r["confidence"] >= t and r["label"] != "refusal"

    print(f"n={n}, {sec:.0f}s per human label ({src}). Labeling everything by hand: {n * sec / 60:.0f} min.\n")
    print("| rule | threshold | sent to human | time saved | final accuracy | unsafe auto-accepted as safe |")
    print("|---|---|---|---|---|---|")
    for t in THRESHOLDS:
        rules = [("conf", lambda i, t=t: a[i]["label"] if ok(a[i], t) else None)]
        if b:
            rules.append(("agree", lambda i, t=t: a[i]["label"]
                          if ok(a[i], t) and ok(b[i], t) and a[i]["label"] == b[i]["label"] else None))
        for name, rule in rules:
            reviewed, acc, leaked = simulate(posts, rule)
            print(f"| {name} | {t} | {reviewed} ({reviewed / n:.0%}) | {1 - reviewed / n:.0%} | {acc:.1%} | {leaked} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("primary")
    ap.add_argument("second", nargs="?")
    ap.add_argument("--data", default="posts")
    args = ap.parse_args()
    main(args.primary, args.second, args.data)
