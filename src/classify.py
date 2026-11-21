"""Run an LLM over every post and save its label, cited rule and confidence.

    python src/classify.py --model claude-haiku-5-5
    python src/classify.py --model claude-haiku-5-5 --backend cli   # uses `claude -p`, no API credits
"""
import argparse
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from common import RESULTS, guide_text, load_posts, preds_path, read_jsonl

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
EMPTY_DIR = tempfile.mkdtemp()  # cli runs here so it can't see the repo (and the answers)


def classify_cli(model, text):
    cmd = ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config",
           "--no-session-persistence", "--output-format", "json",
           "--system-prompt", INSTRUCTIONS.format(guide=guide_text()),
           "--json-schema", json.dumps(Judgment.model_json_schema())]
    # drop CLAUDE_*/ANTHROPIC_* vars so it uses your own login, not a parent session's
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CLAUDE", "ANTHROPIC"))}
    proc = subprocess.run(cmd, input=f"Post:\n{text}", capture_output=True, text=True,
                          cwd=EMPTY_DIR, env=env, timeout=300)
    out = json.loads(proc.stdout)
    if out.get("is_error"):
        raise RuntimeError(out.get("result"))
    data = out.get("structured_output") or json.loads(out["result"])
    return Judgment(**data).model_dump()


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
    ap.add_argument("--backend", choices=["api", "cli"], default="api")
    ap.add_argument("--data", default="posts", help="csv name in data/, e.g. posts_v2")
    args = ap.parse_args()
    judge = classify_cli if args.backend == "cli" else classify

    RESULTS.mkdir(exist_ok=True)
    out = preds_path(args.model, args.data)
    done = {r["id"] for r in read_jsonl(out)}
    todo = [p for p in load_posts(args.data) if p["id"] not in done]
    print(f"{len(todo)} posts to label with {args.model}")

    def run(post):
        # only the text goes to the model, never the id (it leaks the label)
        try:
            return {"id": post["id"], **judge(args.model, post["text"])}
        except (anthropic.APIError, RuntimeError, ValueError, subprocess.TimeoutExpired) as e:
            print(f"{post['id']}: {e}")
            return None

    with ThreadPoolExecutor(args.workers) as pool, out.open("a") as f:
        for row in pool.map(run, todo):
            if row:
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
