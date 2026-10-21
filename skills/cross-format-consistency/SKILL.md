---
name: cross-format-consistency
description: Check that the same patient information delivered in several formats or languages (leaflet, web page, model card, narration, translation) gives the same facts, numbers, risks, pictures and order, and that nothing appears in one format that another cannot show.
---

# Cross-format and cross-language consistency

Use when one message exists in more than one form, for example a leaflet, a web page, a spoken script and a translation, or when a study compares formats and needs them to carry the same information.

## Steps

1. Run `pitk check`: files listed under `pairs` in `.patient-info.json` are compared automatically for numbers, number of main headings and pictures (`pair-*` errors).
2. List the facts in each version as short claims (one per line, with its number and citation). Compare the lists side by side and report:
   - a claim present in one version but not another;
   - a number, denominator or wording of certainty that differs ("may" vs "will");
   - a section in a different order.
3. **Format limits**: list what each format can physically show (a printed model cannot animate; a spoken script cannot show a drawing). Flag any content in one format that the others cannot carry, if the project needs the formats to be equivalent (for example a comparison study).
4. **Translation**: for a translated pair, back-translate the second language briefly for each section and flag changes in meaning, tone (more or less certain, more or less frightening), and any added or dropped hedging.

## Output

Table: claim or element, version A, version B (and C…), problem, suggested fix. Do not change the facts; propose wording that brings the versions together.
