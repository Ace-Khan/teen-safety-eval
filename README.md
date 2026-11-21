# teen-safety-eval

A small benchmark for how well LLMs judge whether content is safe for teens, plus a test of whether an LLM can cut human labeling time.

All data is synthetic. No real teen content and nothing graphic.

## What's here

| path | what |
|---|---|
| `guide/labeling_guide.md` | labeling standard: 6 labels, numbered rules, edge cases |
| `data/posts.csv` | 300 synthetic posts, 50 per label, each tagged with a `trick` (plain, coded, sarcasm, borderline, hard_negative) |
| `data/posts_v2.csv` | 150 "hard" posts, 25 per label: threads, context lines, teasing pressure, buried sentences, messy text |
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

Both models ran through `claude -p` (`classify.py --backend cli`) on all 300 posts. Full output is in [`results/`](results/).

| model | accuracy | unsafe called safe | safe over-flagged | errors with conf ≥ 0.9 |
|---|---|---|---|---|
| Claude Opus 5.5 | 98.7% | 1.2% (3/250) | 2.0% | 0 of 4 |
| Claude Haiku 5.5 | 96.0% | 4.4% (11/250) | 0.0% | 3 of 12 |

False-negative rate by label:

| label | Opus | Haiku |
|---|---|---|
| self_harm | 0.00 | 0.00 |
| grooming | 0.04 | 0.12 |
| dangerous_challenge | 0.00 | 0.04 |
| age_inappropriate | 0.00 | 0.02 |
| misinformation | 0.02 | 0.06 |

Models agree with each other on 96% of posts (kappa 0.95).

### Where they fail

- **Grooming is the weak spot.** 8 of Haiku's 11 misses and 2 of Opus's 3 are grooming. Messages that don't mention age or secrecy outright ("let's move to snap", "turn off location sharing before we video call") read as normal chat.
- **Haiku misses sarcasm.** It calls 13% of unsafe sarcastic posts safe (Opus: 0%). Pressure that sounds like teasing ("sure, go tell your dad about me 🙃") gets read as a joke.
- **Haiku is overconfident when wrong.** A quarter of its errors had confidence ≥ 0.9, including a coded train-track challenge at 0.95. Opus's errors were all ≤ 0.72.
- **Opus only misses borderline posts**, the ones a human could argue about (a stranger offering "a ride, no questions asked").
- **No made-up rules.** Neither model cited a rule ID that isn't in the guide or that belongs to a different label.
- Self-harm was perfect for both, including coded terms and the hyperbole hard negatives.

### Pre-labeling

If Opus pre-labels and a human reviews anything under a confidence threshold:

| threshold | posts a human still checks | time saved | unsafe posts that slip through as "safe" |
|---|---|---|---|
| 0.7 | 14% | 86% | 2 |
| 0.8 | 22% | 78% | 0 |
| 0.9 | 51% | 49% | 0 |

At 0.8, three quarters of the labeling is skipped with no unsafe post missed on this set. Requiring Opus and Haiku to agree costs more review for no extra safety here. The time estimate assumes 15 s per hand label until the timed second pass exists.

### v2: trying to make it harder

v2 targets the v1 weak spots: grooming spread across a short thread, pressure hidden in teasing, a `[context: ...]` line that decides the label (same words, peer vs adult stranger), one risky sentence buried in a normal post, and typos and Spanish. Run with `--data posts_v2`.

| model | v1 accuracy | v2 accuracy | v2 unsafe called safe |
|---|---|---|---|
| Claude Opus 5.5 | 98.7% | 99.3% | 0 of 125 |
| Claude Haiku 5.5 | 96.0% | 96.7% | 2 of 125 |

**It didn't get harder.** Opus missed nothing unsafe, and its one error was a post that arguably fits grooming better than its gold label. Haiku's two misses were a vague goodbye thread ("i won't be around friday... somewhere better") and a messy train-track invite it labeled safe at 0.97 confidence. Grooming, Haiku's worst label in v1, went to perfect recall once the risk was spread over a thread.

The likely reason: when the same model family writes the hard cases, it writes them so the right label can be defended, which means the signal is always there to find. Making this benchmark harder probably needs posts written by people or another model family, or keeping only the posts a model actually gets wrong.

## Limitations

- **The data is probably too easy.** The posts were written with Claude's help, and Claude models are then graded on them. Opus at 98.7% suggests a ceiling. Real posts, or posts from a different author, would be a fairer test.
- Gold labels were set when the posts were written, so the posts and labels share one author's view. The second pass (`label.py`) checks that, and has not been done yet.
- `claude -p` runs through Claude Code, so settings like effort aren't pinned the way an API call would be.
- 50 posts per label is small. Treat differences of a few points as noise.
- Synthetic posts are cleaner than real ones. Real coded language changes fast.
