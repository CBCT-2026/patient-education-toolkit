---
name: ai-reader-panel
description: Simulated user test of a patient material - independent AI readers with different backgrounds answer key-message questions, a separate judge marks found and understood, and pitk panel scores it against the MHRA benchmark (16 of 20). Use as a pre-test before testing with real readers.
---

# AI reader panel

A simulated version of MHRA-style user testing (MHRA, *Best practice guidance on patient information leaflets*: in 2 rounds of 10 readers, each key message must be found and understood by at least 16 of 20). This is a **pre-test**. It finds weak spots cheaply, but it does not replace testing with real people and must not be reported as user testing.

## 1. Key messages and questions

Read the material and write 8 to 15 questions, one per key message. Mix the types:
- finding a fact ("How many people in 100 may get nerve damage?");
- explaining ("Why can taking out this tooth hurt the nerve?");
- applying ("What might you feel if the nerve is damaged?").

For each, write the expected answer and where it is in the material. Show the questions to the user and let them change the list before going on, unless they asked for a fully automatic run.

Save as `reader-panel/questions.json`:
`{"material": "path", "questions": [{"id": "q1", "message": "...", "question": "...", "expected": "...", "where": "..."}]}`

## 2. Readers

Default panel: 20 readers, in 2 rounds of 10. Use the same 10 personas in each round, and give each round a fresh run. Default personas (adjust to the material's audience):

1. Aged 19, student, reads quickly and skims.
2. Aged 72, retired, reads slowly, a little worried.
3. Low health literacy, left school at 16, finds long words hard.
4. Reads English as a second language, intermediate level (CEFR B1).
5. Very anxious about dental treatment, has put it off.
6. Parent reading for their 17-year-old.
7. Dyslexic, prefers pictures and short lines.
8. Had a bad tooth extraction before, distrustful.
9. Busy worker reading on a phone between tasks.
10. Health professional who is not a dentist (for example a nurse).

Run each reader as a **separate, independent agent** (the Agent tool), so that readers cannot see each other's answers. Give each reader only:
- the persona;
- the material as a reader meets it (text in reading order, picture alt texts and captions; for a video, the subtitles and a description of what is on screen);
- the questions, without the expected answers.

Tell the reader to answer in their own words as that person would. For each answer, they should say where they found it, or "not found". They must not use outside knowledge, and must say "I don't know" rather than guess.

## 3. Judge

Run one separate judge agent that sees the expected answers and all reader answers. For each answer it marks:
- `found`: the reader located the information in the material;
- `understood`: the answer matches the expected meaning (wording may differ).

Save as `reader-panel/results.json`:
`{"questions": [...from step 1...], "readers": [{"persona": "...", "round": 1, "answers": {"q1": {"found": true, "understood": false, "answer": "...", "note": "..."}}}]}`

## 4. Score and report

Run `pitk panel reader-panel/results.json` (exit code 1 if any message fails). Report:
- a table of each key message with found, found-and-understood, pass or fail, and which personas missed it;
- for each failed message, the likely cause in the material and a suggested fix;
- the limitation, in these words: "Simulated readers (AI personas) were used as a pre-test; results have not been validated against real readers."

After fixes, run a fresh panel (new agents) rather than reusing earlier answers.
