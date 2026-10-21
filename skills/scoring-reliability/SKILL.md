---
name: scoring-reliability
description: Score a patient material with PEMAT or the CDC Clear Communication Index several times independently and report the mean, spread and agreement (pitk agree), so AI scores can be defended in a paper.
---

# Scoring reliability (repeated AI scoring)

One AI scoring can vary from run to run. This skill runs the same rubric several times and reports how much the runs agree, in the same way two human raters would be compared.

## Steps

1. Choose the instrument: PEMAT-P (print), PEMAT-A/V (audio-visual), or the CDC Clear Communication Index. Use the item wording in the `pemat-review` or `clear-communication-index` skill exactly.
2. Run **3 independent scorings** (5 for a paper), each as a separate agent with the Agent tool. Each agent gets only the material, the rubric and the output format. It does not see the other runs.
3. Each run saves `scoring/<instrument>-run<N>.json`:
   ```json
   {"instrument": "PEMAT-P", "material": "path", "run": 1,
    "sections": {"understandability": {"1": "agree", "2": "disagree", "19": "na"},
                 "actionability": {"20": "disagree", "24": "na"}},
    "reasons": {"2": "one sentence why"}}
   ```
   Answers: PEMAT `agree` / `disagree` / `na`; CDC CCI `yes` / `no` / `na`.
4. Run `pitk agree scoring/<instrument>-run*.json`. For each section it reports every run's score, the mean and SD, the share of items all runs agree on, Fleiss' kappa across runs, and the items the runs disagree on.
5. For each disputed item, read the reasons. Then decide, and say which answer you chose and why. Report the mean score, with SD and kappa, as the result.

## Report wording

"The material was scored with [instrument] by [N] independent runs of [model] using a fixed rubric. Mean understandability was X% (SD Y; all runs agreed on Z% of items; Fleiss' kappa K)." AI scoring has not been validated against expert raters, so say so, or add a human rater for a sample of items.
