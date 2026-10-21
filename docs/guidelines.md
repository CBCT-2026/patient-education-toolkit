# Guidelines behind the toolkit

Each rule in the toolkit comes from one of these sources. Checked 2026-10-21. Re-check the sources before relying on a threshold, because guidance changes.

| Source | What the toolkit takes from it | Where |
| --- | --- | --- |
| NHS digital service manual, content guide: [How we write](https://service-manual.nhs.uk/content/how-we-write) | Sentences up to 20 words; paragraphs up to 3 sentences; reading age 9 to 11 (11 to 14 for hard medical topics); active voice; plain term first, medical term in brackets and explained | hook `en-sentence-length`, `passive-voice`, `jargon`; skill `plain-language-rewrite` |
| NHS: [Voice and tone](https://service-manual.nhs.uk/content/voice-and-tone) | Address the user as "you"; personal, not formal | hook `address-you` |
| NHS: [Numbers, measurements, dates and time](https://service-manual.nhs.uk/content/numbers-measurements-dates-time) | Numerals for numbers; risk as "1 in 10"; avoid percentages; do not mix number formats; put figures in context | hook `percent`, `mixed-denominators`; skill `risk-communication` |
| NHS: [Health literacy](https://service-manual.nhs.uk/content/health-literacy) | More than 6 in 10 adults struggle with numbers; readability tools only help to prioritise | README caveat; the hooks are a first filter, the skills and user testing decide |
| AHRQ [PEMAT-P / PEMAT-A/V](https://www.ahrq.gov/health-literacy/patient-education/pemat-p.html) (Shoemaker et al. 2014) | 17 understandability + 7 actionability items, agree/disagree/N/A, score = agree / applicable x 100; 70% is a common cut-off | skill `pemat-review` |
| CDC [Clear Communication Index](https://www.cdc.gov/ccindex/) (score sheet: [CDC Stacks 21458](https://stacks.cdc.gov/view/cdc/21458/cdc_21458_DS1.pdf)) | 4 open questions + 20 scored items in parts A-D; target 90 or above | skill `clear-communication-index` |
| International Patient Decision Aid Standards (IPDAS) | Natural frequencies with the same denominator, absolute not only relative risk, time frame, positive and negative framing, uncertainty | skill `risk-communication`, hook `relative-risk`, `verbal-risk` |
| ISO 24495-1:2023 Plain language | Relevant, findable, understandable, usable | skill `plain-language-rewrite` |
| Patient Information Forum (PIF) TICK criteria | Production process: evidence, sources listed, user involvement, dates and review date, contact details | skill `patient-info-review` (process checklist); hook `require` (presence of date, sources, contact) |
| 出入国在留管理庁・文化庁「在留支援のためのやさしい日本語ガイドライン」(2020) | 1文1情報; 文を短く; 二重否定を避ける; 敬語は「です・ます」まで; カタカナ語・オノマトペを避ける; 専門用語は説明を付ける; イラスト・写真を使う | hook `ja-sentence-length`, `ja-keigo`, `double-negative`, `jargon`; skill `yasashii-nihongo` |
| 文部科学省「学年別漢字配当表」(2020) | 1,026 kanji taught in grades 1-6 | hook `ja-kanji` (data/kyouiku_kanji_2020.txt) |

## Where the guidance disagrees

- **Visual aids for risk.** IPDAS supports icon arrays; the NHS numbers page says the evidence is not yet strong enough to recommend visual aids for statistics. The toolkit does not require them. The `risk-communication` skill asks the author to decide and record why.
- **Reading formulas.** FKGL (English) and sentence length (Japanese) are rough. NHS warns against relying on readability tools. Use the hook as a first filter, then the review skills, then test with real readers.
- **"You" in Japanese.** English guidance says to address the reader as "you". Natural Japanese usually leaves the subject out; overusing あなた sounds cold or odd. The default for Japanese is therefore `ja_address_reader: "omit"` (no check).
