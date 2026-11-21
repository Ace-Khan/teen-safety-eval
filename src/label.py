"""Second-pass labeling in the terminal. Shows a shuffled sample with no ids or labels.

    python src/label.py --n 60

Saves to data/annotator_b.csv as you go, so you can quit and resume.
"""
import argparse
import csv
import random
import time

from common import DATA, LABELS, load_posts

OUT = DATA / "annotator_b.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    posts = load_posts()
    random.Random(args.seed).shuffle(posts)
    sample = posts[:args.n]

    done = set()
    if OUT.exists():
        done = {r["id"] for r in csv.DictReader(OUT.open())}
    new_file = not OUT.exists()

    menu = "  ".join(f"{i + 1}={lab}" for i, lab in enumerate(LABELS))
    with OUT.open("a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["id", "label", "seconds"])
        for k, post in enumerate(sample):
            if post["id"] in done:
                continue
            print(f"\n[{k + 1}/{len(sample)}] {post['text']}\n{menu}")
            start = time.time()
            choice = ""
            while choice not in [str(i + 1) for i in range(len(LABELS))]:
                choice = input("> ").strip()
                if choice == "q":
                    return
            w.writerow([post["id"], LABELS[int(choice) - 1], round(time.time() - start, 1)])
            f.flush()


if __name__ == "__main__":
    main()
