"""Where do models fail? Breaks errors down by trick, confusion, overconfidence and made-up rules.

    python src/gaps.py claude-opus-5-5 claude-haiku-5-5
"""
import sys
from collections import Counter

from common import LABELS, RESULTS, UNSAFE, load_posts, read_jsonl, rule_ids

PREFIX = {"SH": "self_harm", "GR": "grooming", "DC": "dangerous_challenge",
          "AI": "age_inappropriate", "MI": "misinformation", "SF": "safe"}
TRICKS = ["plain", "coded", "sarcasm", "borderline", "hard_negative"]


def analyze(model, posts):
    preds = {r["id"]: r for r in read_jsonl(RESULTS / f"preds_{model}.jsonl")}
    rows = [(p, preds[p["id"]]) for p in posts if p["id"] in preds]
    valid_rules = rule_ids()
    out = [f"### {model}", ""]

    out += ["Accuracy by trick:", "", "| trick | n | accuracy | unsafe called safe |", "|---|---|---|---|"]
    for t in TRICKS:
        sub = [(p, r) for p, r in rows if p["trick"] == t]
        if not sub:
            continue
        acc = sum(p["label"] == r["label"] for p, r in sub) / len(sub)
        uns = [(p, r) for p, r in sub if p["label"] in UNSAFE]
        miss = f"{sum(r['label'] == 'safe' for _, r in uns) / len(uns):.0%}" if uns else "-"
        out.append(f"| {t} | {len(sub)} | {acc:.0%} | {miss} |")

    errors = Counter((p["label"], r["label"]) for p, r in rows if p["label"] != r["label"])
    out += ["", "Most common confusions (gold -> predicted):", ""]
    out += [f"- {g} -> {pr}: {c}" for (g, pr), c in errors.most_common(6)]

    wrong = [(p, r) for p, r in rows if p["label"] != r["label"] and r["confidence"] is not None]
    overconf = [(p, r) for p, r in wrong if r["confidence"] >= 0.9]
    out += ["", f"Wrong answers: {len(wrong)}. Wrong with confidence >= 0.9: {len(overconf)} "
                f"({len(overconf) / max(len(wrong), 1):.0%} of errors)."]

    cited = [(p, r) for p, r in rows if r["rule_id"]]
    fake = [(p, r) for p, r in cited if r["rule_id"] not in valid_rules]
    # rule exists but belongs to a different label than the one picked
    mismatch = [(p, r) for p, r in cited if r["rule_id"] in valid_rules
                and PREFIX.get(r["rule_id"].split("-")[0], r["label"]) != r["label"]]
    out.append(f"Cited a rule that isn't in the guide: {len(fake)}. "
               f"Cited a rule from a different category than its label: {len(mismatch)}.")
    for p, r in fake[:5]:
        out.append(f"  - {p['id']} cited `{r['rule_id']}`")

    missed = [(p, r) for p, r in rows if p["label"] in UNSAFE and r["label"] == "safe"]
    out += ["", f"Unsafe posts called safe ({len(missed)}):", ""]
    out += [f"- `{p['id']}` ({p['trick']}, conf {r['confidence']}): {p['text']}" for p, r in missed]
    return "\n".join(out) + "\n"


def confusion(model, posts):
    preds = {r["id"]: r["label"] for r in read_jsonl(RESULTS / f"preds_{model}.jsonl")}
    cols = LABELS + ["refusal"]
    out = [f"| gold \\ pred | " + " | ".join(c[:8] for c in cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for g in LABELS:
        c = Counter(preds[p["id"]] for p in posts if p["label"] == g and p["id"] in preds)
        out.append(f"| {g} | " + " | ".join(str(c[x]) for x in cols) + " |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    posts = load_posts()
    for m in sys.argv[1:]:
        print(analyze(m, posts))
        print(confusion(m, posts))
