---
name: patient-info-review
description: Review and improve a patient information document (leaflet, web page, consent text, narration) in English or Japanese against NHS, PEMAT, CDC Clear Communication Index, IPDAS and やさしい日本語 guidance. Use when asked to check, review, improve or score patient-facing health material.
---

# Patient information review

Run the steps in order. Do not skip step 1: the automatic checks are cheap and catch most mechanical problems.

## 1. Automatic checks

If `pitk` is not installed, install it first: `pip install git+https://github.com/CBCT-2026/patient-education-toolkit`.

Run `pitk check <files>` (or with no files to check everything listed in `.patient-info.json`).
If the project has no `.patient-info.json`, offer to create one from `examples/patient-info.json` and ask the user:
- which files are patient-facing and in which language;
- which files are translations of each other (`pairs`);
- whether the text should speak to the reader as "you" (NHS and CDC recommend it; `address_reader`);
- the reading target (default: FKGL 6 and SMOG 6, Flesch Reading Ease 70 or more, 20 words per sentence; jReadability 3.5 or more; Japanese 50 characters per sentence, grade 1-6 kanji).

Every `error` must be fixed or explicitly accepted by the user (then add the term to `jargon_allow` or relax the rule in the config, with a note why). Warnings need judgement.

## 2. Judgement reviews

Before scoring, write down the CDC open questions: primary audience, what is known about their health literacy, the communication objective, and the one main message. Then use, as relevant:

- `pemat-review`: understandability and actionability scores.
- `clear-communication-index`: CDC score (target 90+).
- `risk-communication`: whenever the text gives a risk, chance or side effect.
- `plain-language-rewrite`: English wording and structure.
- `yasashii-nihongo`: Japanese wording.
- `cross-format-consistency`: when the same content exists in more than one format or language.
- `dental-consent-content`: when the material is about a dental or oral surgery procedure.

## 3. PIF TICK process check (report only)

Say whether the material has: the evidence behind each fact, a source list, the date written and next review date, who wrote it and a contact, and user involvement (people from the audience read it before release). Missing items go in the report; do not invent them.

## 4. Report, then edit

Give the user one table: section, problem, rule or item it fails, suggested new wording. Keep the facts, numbers and citations unchanged unless a fact is wrong (then say so separately with the source).
Apply edits only when the user asked for edits, or after they agree. After editing, run step 1 again and show the before and after scores (`pitk check --scores`, PEMAT, CCI).

Never claim the material is "compliant" or "approved": these tools support, not replace, testing with real readers and the organisation's own sign-off.
