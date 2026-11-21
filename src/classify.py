"""Run an LLM over every post and save its label, cited rule and confidence.

    python src/classify.py --model claude-haiku-5-5
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from common import RESULTS, guide_text, load_posts, read_jsonl

INSTRUCTIONS = """You are a content moderator for a social app used by teens (13-17).
Label the post using ONLY the labeling guide below. Cite the single rule ID that decides
your label (e.g. SH-1, SF-1). Give your confidence that the label is correct, from 0 to 1.

<guide>
{guide}
</guide>"""


class Judgment(BaseModel):
    label: Literal["self_harm", "grooming", "dangerous_challenge", "age_inappropriate", "misinformation", "safe"]
    rule_id: str = Field(description="rule ID from the guide, like SH-2")
    confidence: float = Field(description="0 to 1")
    reason: str = Field(description="one short sentence")


client = anthropic.Anthropic()


def classify(model, text):
    resp = client.messages.parse(
        model=model,
        max_tokens=4000,
        system=[{
            "type": "text",
            "text": INSTRUCTIONS.format(guide=guide_text()),
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": f"Post:\n{text}"}],
        output_config={"effort": "low"},
        output_format=Judgment,
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        return {"label": "refusal", "rule_id": None, "confidence": None, "reason": resp.stop_reason}
    return resp.parsed_output.model_dump()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"preds_{args.model}.jsonl"
    done = {r["id"] for r in read_jsonl(out)}
    todo = [p for p in load_posts() if p["id"] not in done]
    print(f"{len(todo)} posts to label with {args.model}")

    def run(post):
        # only the text goes to the model, never the id (it leaks the label)
        try:
            return {"id": post["id"], **classify(args.model, post["text"])}
        except anthropic.APIError as e:
            print(f"{post['id']}: {e}")
            return None

    with ThreadPoolExecutor(args.workers) as pool, out.open("a") as f:
        for row in pool.map(run, todo):
            if row:
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
