"""Per-category precision, recall and false-negative rate for one model's predictions.

    python src/metrics.py claude-opus-5-5
"""
import sys

from common import LABELS, RESULTS, UNSAFE, load_posts, read_jsonl


def load_pairs(model):
    gold = {p["id"]: p["label"] for p in load_posts()}
    preds = {r["id"]: r for r in read_jsonl(RESULTS / f"preds_{model}.jsonl")}
    return [(gold[i], preds[i]["label"]) for i in gold if i in preds]


def per_label(pairs):
    rows = []
    for lab in LABELS:
        tp = sum(g == lab and p == lab for g, p in pairs)
        fp = sum(g != lab and p == lab for g, p in pairs)
        fn = sum(g == lab and p != lab for g, p in pairs)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        rows.append({"label": lab, "n": tp + fn, "precision": prec, "recall": rec, "fnr": 1 - rec})
    return rows


def summary(pairs):
    acc = sum(g == p for g, p in pairs) / len(pairs)
    unsafe = [(g, p) for g, p in pairs if g in UNSAFE]
    # the error we care most about: unsafe content that gets called safe
    missed = sum(p == "safe" for _, p in unsafe) / len(unsafe)
    safe = [(g, p) for g, p in pairs if g == "safe"]
    overflag = sum(p != "safe" for _, p in safe) / len(safe)
    refusals = sum(p == "refusal" for _, p in pairs)
    return {"n": len(pairs), "accuracy": acc, "unsafe_called_safe": missed,
            "safe_flagged": overflag, "refusals": refusals}


def report(model):
    pairs = load_pairs(model)
    s = summary(pairs)
    lines = [f"### {model}", "",
             f"n={s['n']}, accuracy {s['accuracy']:.1%}, unsafe called safe {s['unsafe_called_safe']:.1%}, "
             f"safe over-flagged {s['safe_flagged']:.1%}, refusals {s['refusals']}", "",
             "| label | n | precision | recall | FNR |", "|---|---|---|---|---|"]
    for r in per_label(pairs):
        lines.append(f"| {r['label']} | {r['n']} | {r['precision']:.2f} | {r['recall']:.2f} | {r['fnr']:.2f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    for m in sys.argv[1:]:
        print(report(m))
