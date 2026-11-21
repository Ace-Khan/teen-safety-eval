"""Cohen's kappa between the gold labels and a second pass (or between two models).

    python src/agreement.py                       # gold vs data/annotator_b.csv
    python src/agreement.py --models a b          # model a vs model b
"""
import argparse
import csv
from collections import Counter

from common import DATA, RESULTS, load_posts, read_jsonl


def kappa(a, b):
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[k] * cb[k] for k in ca) / (n * n)
    return observed, (observed - expected) / (1 - expected) if expected < 1 else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs=2)
    args = ap.parse_args()

    if args.models:
        x = {r["id"]: r["label"] for r in read_jsonl(RESULTS / f"preds_{args.models[0]}.jsonl")}
        y = {r["id"]: r["label"] for r in read_jsonl(RESULTS / f"preds_{args.models[1]}.jsonl")}
        name = " vs ".join(args.models)
    else:
        x = {p["id"]: p["label"] for p in load_posts()}
        y = {r["id"]: r["label"] for r in csv.DictReader((DATA / "annotator_b.csv").open())}
        name = "gold vs annotator B"

    ids = sorted(set(x) & set(y))
    obs, k = kappa([x[i] for i in ids], [y[i] for i in ids])
    print(f"{name}: n={len(ids)}, raw agreement {obs:.1%}, Cohen's kappa {k:.2f}")
    for i in ids:
        if x[i] != y[i]:
            print(f"  {i}: {x[i]} / {y[i]}")


if __name__ == "__main__":
    main()
