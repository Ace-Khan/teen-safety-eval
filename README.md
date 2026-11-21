# teen-safety-eval

A small benchmark for how well LLMs judge whether content is safe for teens, plus a test of whether an LLM can cut human labeling time.

All data is synthetic. No real teen content and nothing graphic.

## What's here

| path | what |
|---|---|
| `guide/labeling_guide.md` | labeling standard: 6 labels, numbered rules, edge cases |
| `data/posts.csv` | 300 synthetic posts, 50 per label, each tagged with a `trick` (plain, coded, sarcasm, borderline, hard_negative) |
| `data/annotator_b.csv` | second-pass labels on a 60-post sample (created by `label.py`) |
| `src/classify.py` | runs a Claude model as a classifier (label, cited rule, confidence) |
| `src/metrics.py` | precision, recall and false-negative rate for each label |
| `src/agreement.py` | Cohen's kappa, gold vs second pass or model vs model |
| `src/gaps.py` | errors by trick, confusions, overconfidence, made-up rule citations |
| `src/prelabel.py` | simulates LLM pre-labeling with confidence and agreement routing |

## Labels

`self_harm`, `grooming`, `dangerous_challenge`, `age_inappropriate`, `misinformation`, `safe`. One label per post, taking the highest in that order when more than one applies. A false negative (unsafe called safe) is treated as the costly error.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd src

python label.py --n 60                 # your second pass, timed
python agreement.py                    # kappa vs gold

python classify.py --model claude-opus-5-5
python classify.py --model claude-haiku-5-5
python metrics.py claude-opus-5-5 claude-haiku-5-5
python gaps.py claude-opus-5-5 claude-haiku-5-5
python prelabel.py claude-opus-5-5 claude-haiku-5-5
```

Only the post text is sent to the model, never the id (ids start with the label prefix).

## Results

_Not run yet._

## Limitations

- Gold labels were set when the posts were written, so the posts and labels share one author's view. The second pass checks that.
- 50 posts per label is small. Treat differences of a few points as noise.
- Synthetic posts are cleaner than real ones. Real coded language changes fast.
