### claude-opus-5-5

n=300, accuracy 98.7%, unsafe called safe 1.2%, safe over-flagged 2.0%, refusals 0

| label | n | precision | recall | FNR |
|---|---|---|---|---|
| self_harm | 50 | 1.00 | 1.00 | 0.00 |
| grooming | 50 | 1.00 | 0.96 | 0.04 |
| dangerous_challenge | 50 | 1.00 | 1.00 | 0.00 |
| age_inappropriate | 50 | 1.00 | 1.00 | 0.00 |
| misinformation | 50 | 0.98 | 0.98 | 0.02 |
| safe | 50 | 0.94 | 0.98 | 0.02 |

### claude-haiku-5-5

n=300, accuracy 96.0%, unsafe called safe 4.4%, safe over-flagged 0.0%, refusals 0

| label | n | precision | recall | FNR |
|---|---|---|---|---|
| self_harm | 50 | 0.98 | 1.00 | 0.00 |
| grooming | 50 | 1.00 | 0.88 | 0.12 |
| dangerous_challenge | 50 | 1.00 | 0.96 | 0.04 |
| age_inappropriate | 50 | 1.00 | 0.98 | 0.02 |
| misinformation | 50 | 1.00 | 0.94 | 0.06 |
| safe | 50 | 0.82 | 1.00 | 0.00 |

