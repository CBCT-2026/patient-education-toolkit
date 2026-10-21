---
name: plain-language-rewrite
description: Rewrite English patient information in plain language following the NHS content guide and ISO 24495-1 (you, active voice, short sentences, plain words first, chunked with clear headings), keeping all facts and citations.
---

# Plain language rewrite (English)

## Rules

- **Talk to the reader as "you"** (NHS voice and tone), unless the project config says `address_reader: "neutral"`. "If you have a wisdom tooth taken out, you may…", not "Patients may…".
- **Active voice**: say who does what. "The surgeon takes out the tooth", not "The tooth is removed".
- **Sentences up to 20 words; paragraphs up to 3 sentences** (NHS). One idea per sentence.
- **Reading age 9 to 11** (FKGL about 4-6). For hard medical content, 11 to 14 at most.
- **Plain word first, medical word in brackets, explained once**: "lower jaw nerve (inferior alveolar nerve)". Only keep a medical term if the reader will hear it from their dentist or doctor or need it to search.
- **Headings that say what the section answers**, ideally as questions ("What can go wrong?").
- **Lists** for 3 or more items.
- **Numbers as numerals**; risks as "X in 100" (see `risk-communication`).
- **No metaphors, idioms, double negatives or capitals for emphasis** (use bold sparingly).
- **Be precise**: name symptoms ("numb, tingling or painful lip"), not "discomfort".
- **ISO 24495-1 check**: is every part relevant to this reader, easy to find, easy to understand, and easy to use?

## How to rewrite

1. Keep every fact, number, citation marker and link. Do not add facts.
2. Rewrite section by section; keep section order unless the main message is not at the top.
3. Run `pitk check` after each file and fix errors.
4. Show the user before and after for each changed sentence, or a diff, and the FKGL before and after.
