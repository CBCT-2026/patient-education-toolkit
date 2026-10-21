---
name: risk-communication
description: Check and rewrite how a patient document states risks, chances and side effects (natural frequencies, same denominator, absolute risk, time frame, uncertainty), following IPDAS, NHS and CDC guidance.
---

# Risk communication

Use on every sentence that gives a chance, risk, rate or side effect.

## Rules

1. **Natural frequencies**: "about 7 in 100 people", not "7%" or "0.07" (NHS numbers guide; IPDAS).
2. **Same denominator** throughout a document: if one risk is "in 100", give the others "in 100" too ("1 in 1,000" becomes "less than 1 in 100" only if that stays accurate; otherwise keep "in 1,000" for every rare risk and say why). The `mixed-denominators` hook flags this.
3. **Absolute, not only relative**: "doubles the risk" must also say "from 1 in 100 to 2 in 100".
4. **Who and when**: say which people the number applies to ("for teeth close to the nerve") and over what time ("after the operation", "after 6 months").
5. **Both framings for key risks** where space allows: "7 in 100 have nerve damage; 93 in 100 do not".
6. **Uncertainty**: say if studies disagree ("rates vary between studies, but about…"). Do not give false precision (no decimals for patients).
7. **Words with numbers**: verbal labels like "rare" or "common" are read very differently by different people. Use them only next to the number (the `verbal-risk` hook flags labels without a number).
8. **Visuals**: icon arrays (100 figures) are supported by IPDAS, but the NHS numbers guide says the evidence is not yet strong enough to recommend visual aids. Decide with the author, and if used: one icon array per risk, same 100-figure grid, plain caption.
9. **Balance**: give the benefit or reason for the treatment near the risk, and the options (including doing nothing or monitoring) where relevant (CDC CCI item 19).
10. **Accuracy first**: never round in a way that changes the meaning; keep the citation for every number.

## Output

Table: original sentence, rule(s) it breaks, suggested sentence. List any number without a source.
