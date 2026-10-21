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

## Dentistry

No dental body publishes guidance on *how to write* patient materials. The dental sources below cover *what to tell patients* for consent, and are used by the `dental-consent-content` skill.

| Source | What the toolkit takes from it | Where |
| --- | --- | --- |
| RCS England, Faculty of Dental Surgery. [Parameters of care for patients undergoing mandibular third molar surgery](https://www.rcseng.ac.uk/-/media/Files/RCS/FDS/3rd-molar-guidelines--April-2021-v3.pdf) (2020) | Material risks (nerve injury, dry socket and others), alternatives including coronectomy, risks of deferring or declining, age and nerve proximity as risk factors; written information recommended | skill `dental-consent-content` items 3-7 |
| Australian Dental Association. [Guidelines for Consent for Care in Dentistry](https://adanstaging.ada.org.au/getmedia/50907ede-4a19-4530-b864-71732fc557e9/ADA_Guidelines_Consent-for-care.pdf) (2020) | Plain non-technical language; disclose material risks, naming nerve damage in oral surgery; written information alone is not enough, so check understanding | skill `dental-consent-content` items 2, 3, 9 |
| 日本歯科麻酔学会ほか. [歯科治療による下歯槽神経・舌神経損傷の診断とその治療に関するガイドライン](https://minds.jcqhc.or.jp/?p=1745) (2019) | Japanese clinical guideline on inferior alveolar and lingual nerve injury: what the injury is and how it is managed | skill `dental-consent-content` items 3, 4 |
| Lewis MA, Newton JT. [An evaluation of the quality of commercially produced patient information leaflets](https://www.nature.com/articles/4813828). *Br Dent J* 2006;201:114-117 | Aim stated first, patient-centred, option of no treatment, sources and dates | skill `dental-consent-content` items 1, 5, 10 |
| Montgomery v Lanarkshire Health Board [2015] UKSC 11 | What counts as a material risk | skill `dental-consent-content` |

## Video, narration, colour and AI scoring

| Source | What the toolkit takes from it | Where |
| --- | --- | --- |
| Netflix Timed Text Style Guides: [General requirements](https://backlothelp.netflix.com/hc/en-us/articles/215758617), [English (USA)](https://backlothelp.netflix.com/hc/en-us/articles/217350977) and [Japanese](https://backlothelp.netflix.com/hc/en-us/articles/215767517) | English: 42 characters a line, 2 lines, 20 characters a second (adult); Japanese: 16 characters a line, 4 characters a second; 5/6 s to 7 s on screen | hook `sub-line-length`, `sub-reading-speed`, `sub-duration` |
| BBC [Subtitle guidelines](https://www.bbc.co.uk/accessibility/forproducts/guides/subtitles/) | About 160 to 180 words a minute for subtitles; break lines at natural points | skill guidance; the default speaking rate (150 words a minute) is a little slower for health content |
| W3C [WCAG 2.2](https://www.w3.org/TR/WCAG22/), 1.4.3 Contrast (Minimum) and 1.1.1 Non-text Content | Contrast 4.5:1 for text, 3:1 for large text (24 px, or 18.7 px bold); alt text that serves the same purpose as the image | hook `contrast`, `img-alt`, `img-alt-quality`; `pitk contrast` |
| Machado GM, Oliveira MM, Fernandes LAF. A physiologically-based model for simulation of color vision deficiency. *IEEE Trans Vis Comput Graph* 2009;15(6):1291-1298 | Matrices for protanopia, deuteranopia and tritanopia (severity 1.0) | `pitk cvd` |
| MHRA. [Best practice guidance on patient information leaflets](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/946602/Best_practice_guidance_on_patient_information_leaflets.pdf) | User testing: 2 rounds of 10 readers; each key message found and understood by 16 of 20 | skill `ai-reader-panel` (simulated), `pitk panel` |
| Fleiss JL. Measuring nominal scale agreement among many raters. *Psychol Bull* 1971;76(5):378-382 | Agreement between repeated scorings | skill `scoring-reliability`, `pitk agree` |

Limits: spoken length is an estimate (measure the recording); the subtitle limits are industry style rules, not health-literacy evidence; simulated readers and repeated AI scoring have **not** been validated against real readers or expert raters, so report them as pre-tests.

## Where the guidance disagrees

- **Visual aids for risk.** IPDAS supports icon arrays; the NHS numbers page says the evidence is not yet strong enough to recommend visual aids for statistics. The toolkit does not require them. The `risk-communication` skill asks the author to decide and record why.
- **Reading formulas.** All the formulas below are rough. NHS warns against relying on readability tools, and the formulas also disagree with each other (SMOG usually gives a grade 1 to 3 higher than FKGL for the same text). Use the hook as a first filter, then the review skills, then test with real readers.
- **"You" in Japanese.** English guidance says to address the reader as "you". Natural Japanese usually leaves the subject out; overusing あなた sounds cold or odd. The default for Japanese is therefore `ja_address_reader: "omit"` (no check).

## Readability formulas

`pitk check --scores` prints every score. FKGL is the main English measure. SMOG is a second gate, and Flesch Reading Ease gives a warning. The other scores are reported only. Each threshold is a setting in `.patient-info.json`.

| Formula | Source | What it counts | Used as | Default |
| --- | --- | --- | --- | --- |
| Flesch-Kincaid grade level (FKGL) | Kincaid JP, Fishburne RP, Rogers RL, Chissom BS. *Derivation of new readability formulas for Navy enlisted personnel.* Research Branch Report 8-75, Naval Technical Training Command, 1975 | words per sentence, syllables per word | **main measure**, per section, rule `en-fkgl` | error above 6 (`en_max_fkgl`) |
| SMOG grade | McLaughlin GH. SMOG grading: a new readability formula. *Journal of Reading* 1969;12(8):639-646 | words of 3 or more syllables per sentence | gate, whole file, rule `en-smog` | error above 6 (`en_max_smog`) |
| Flesch Reading Ease (FRE) | Flesch R. A new readability yardstick. *Journal of Applied Psychology* 1948;32(3):221-233 | the same as FKGL, on a 0-100 scale where higher is easier (70-80 "fairly easy", 60-70 "standard") | warning, whole file, rule `en-fre` | warning below 70 (`en_min_fre`) |
| Gunning Fog index | Gunning R. *The Technique of Clear Writing.* McGraw-Hill, 1952 | words per sentence, share of words with 3 or more syllables | report only | none |
| Coleman-Liau index | Coleman M, Liau TL. A computer readability formula designed for machine scoring. *Journal of Applied Psychology* 1975;60(2):283-284 | letters and sentences per 100 words (no syllables) | report only | none |
| Automated Readability Index (ARI) | Smith EA, Senter RJ. *Automated Readability Index.* AMRL-TR-66-220, Aerospace Medical Research Laboratories, Wright-Patterson AFB, 1967 | characters per word, words per sentence | report only | none |
| jReadability (Japanese) | 李在鎬 (Lee Jae-ho). 日本語教育のための文章難易度に関する研究. 『早稲田日本語教育学』21, 2016 ([PDF](https://waseda.repo.nii.ac.jp/record/35923/files/WasedaNihongoKyoikugaku_21_Lee.pdf)); Hasebe Y, Lee J-H. Introducing a readability evaluation system for Japanese language education. CASTEL/J 2015 ([slides](https://www.yohasebe.com/assets/docs/Hasebe_Lee_2015_CASTELJ.pdf)); online system [jreadability.net](https://jreadability.net) | 11.724 − 0.056 × mean sentence length (words) − 0.126 × % kango − 0.042 × % wago − 0.145 × % verbs − 0.044 × % particles | warning, whole file, rule `ja-jread` | warning below 3.5 (`ja_min_jread`) |

The English scores come from `textstat` 0.7.3. Scores are worked out on the whole file, except FKGL, which is per section so that one hard section cannot hide behind easy ones. Headings and list items count as sentences.

jReadability levels (Hasebe & Lee 2015; higher is easier): 5.5-6.4 初級前半 lower elementary, 4.5-5.4 初級後半 upper elementary, 3.5-4.4 中級前半 lower intermediate, 2.5-3.4 中級後半 upper intermediate, 1.5-2.4 上級前半 lower advanced, 0.5-1.4 上級後半 upper advanced. The default warning at 3.5 means "lower intermediate or easier".

### Limits

- **All formulas** measure only word and sentence length (and, for Japanese, word types). They ignore layout, pictures, order, tone and whether the reader knows the topic. A short, wrong or confusing text can still score well.
- **Short texts** give unstable scores. SMOG was built on samples of 30 sentences: below 3 sentences the toolkit does not report it. For a leaflet shorter than 30 sentences, treat SMOG as a rough guide.
- **Formulas disagree.** SMOG predicts the grade for full understanding, so it is usually 1 to 3 grades higher than FKGL for the same text. Reports in health literacy often prefer SMOG for health information for this reason (for example Wang LW et al. *Res Social Adm Pharm* 2013;9(5):503-516). FKGL stays the main measure here, because the NHS reading age (9 to 11) maps most directly onto it.
- **Syllable counting** in textstat uses a hyphenation dictionary, so it can be off by one for some words, and numbers count as one short word.
- **Medical words** such as "nerve" or "jaw" are short and score as easy. Long but familiar words such as "information" score as hard.
- **jReadability** was built on Japanese textbooks for learners of Japanese, so it measures difficulty for learners rather than for native readers. It depends on the word splitting of the morphological analyser (UniDic, via `fugashi` and `unidic-lite`), so scores can differ a little from the jreadability.net web system. The counting follows the open-source [jreadability](https://github.com/joshdavham/jreadability) package (MIT licence): punctuation counts as a word, and verbs exclude 非自立可能 forms (the あり of あります). The tests check the score against that package. Without `fugashi` and `unidic-lite` the score is skipped and the report says so.
- **Obi-2** (Sato S, Matsuyoshi S, Kondoh Y. Automatic assessment of Japanese text readability based on a textbook corpus. LREC 2008) is not included. It needs the authors' trained model, which is only available through their web service, so it cannot run offline.
