n=300, 15s per human label (assumed). Labeling everything by hand: 75 min.

| rule | threshold | sent to human | time saved | final accuracy | unsafe auto-accepted as safe |
|---|---|---|---|---|---|
| conf | 0.5 | 1 (0%) | 100% | 99.0% | 3 |
| agree | 0.5 | 12 (4%) | 96% | 99.3% | 2 |
| conf | 0.7 | 41 (14%) | 86% | 99.3% | 2 |
| agree | 0.7 | 70 (23%) | 77% | 99.7% | 1 |
| conf | 0.8 | 65 (22%) | 78% | 100.0% | 0 |
| agree | 0.8 | 92 (31%) | 69% | 100.0% | 0 |
| conf | 0.9 | 152 (51%) | 49% | 100.0% | 0 |
| agree | 0.9 | 168 (56%) | 44% | 100.0% | 0 |
| conf | 0.95 | 226 (75%) | 25% | 100.0% | 0 |
| agree | 0.95 | 240 (80%) | 20% | 100.0% | 0 |
