# patient-education-toolkit

Claude Code skills and deterministic hooks for writing **patient education materials** (leaflets, web pages, consent text, spoken scripts) in **English and Japanese**, based on current guidance: the NHS content guide, AHRQ PEMAT, the CDC Clear Communication Index, IPDAS risk communication, ISO 24495-1 plain language, and 出入国在留管理庁・文化庁「やさしい日本語ガイドライン」. Sources and how each rule maps to them: [docs/guidelines.md](docs/guidelines.md).

It has two parts:

- **Hooks (deterministic):** every time Claude edits a listed file, a Python checker runs and reports problems. Errors are sent back to Claude, which has to fix them before carrying on. The same checker runs on the command line or in CI.
- **Skills (judgement):** step-by-step reviews Claude follows for what a script cannot judge: PEMAT scoring, the CDC index, risk wording, plain-language and やさしい日本語 rewrites, and consistency across formats and languages.

The checks are a first filter, not proof of quality. The NHS advises against relying on readability formulas. Always test the material with people from its audience.

## What the hook checks

| Rule | English | Japanese | Default |
| --- | --- | --- | --- |
| Reading level | Flesch-Kincaid grade per section ≤ 6 (main measure); SMOG grade ≤ 6 for the whole file | | error |
| Reading ease | Flesch Reading Ease ≥ 70 | jReadability ≥ 3.5 (lower intermediate or easier) | warning |
| Other scores | Gunning Fog, Coleman-Liau, ARI (`pitk check --scores`) | | report only |
| Sentence length | ≤ 20 words | ≤ 50 characters | warning |
| Kanji | | only the 1,026 grade 1-6 kanji (MEXT 2020), or the 2,136 jouyou kanji | error |
| Kanji share | | ≤ 35% of characters per section | warning |
| Jargon | ~80 medical terms with plain alternatives, plus your own | ~40 terms | error (unless explained in brackets or after "medical name is", or allowed in config) |
| Talking to the reader | "the patient", "patients" → "you"; or flags "you" in neutral mode | flags あなた if set to neutral | warning |
| Passive voice | heuristic | | warning |
| Risk numbers | percentages, mixed denominators ("in 100" and "in 1,000"), "rare"/"common" without a number, relative risk without absolute | same | warning |
| Undefined acronyms, capitals for emphasis, double negatives | ✓ | 二重否定, 敬語 (いただく, ございます) | warning |
| Images without alt text, "click here" links | ✓ | ✓ | error / warning |
| Risk numbers against sources | every "X in N" / % must be in the project's claim map and cite one of its sources | same (100人中X人) | error / warning |
| Alt text quality | file names, "image", "picture of …", over 150 characters | same | warning |
| Spoken scripts | estimated length (150 words a minute) against a time limit | 5.5 characters a second | error |
| Subtitles (.vtt, .srt) | ≤ 42 characters a line, ≤ 2 lines, ≤ 20 characters a second, 0.83-7 s on screen | ≤ 16 characters a line, ≤ 4 a second | warning |
| Labels across formats | e.g. video labels and web page labels use the same names | same | warning |
| Colour contrast | listed text colours meet WCAG 2.2 (4.5:1, or 3:1 for large text) | same | error |
| Language pairs | same numbers, same number of main headings, same pictures in the same order | | error |
| Required text | e.g. date written, contact (PIF TICK basics) | | warning |

Every threshold and severity can be changed per project.

## Install

**As a Claude Code plugin (skills + hook):**

```
/plugin marketplace add CBCT-2026/patient-education-toolkit
/plugin install patient-education-toolkit@patient-education-toolkit
```

The hook needs Python 3.9+ with `beautifulsoup4` and `textstat==0.7.3` (`pip install -r requirements.txt`). textstat is pinned because newer versions need an extra dictionary download. The Japanese readability score also needs `fugashi` and `unidic-lite` (`pip install fugashi unidic-lite`). Without them it is skipped.

**Or as a command-line tool only:**

```
pip install git+https://github.com/CBCT-2026/patient-education-toolkit
pitk check leaflet.html
```

To use the hook without the plugin, copy `examples/settings.json` into your project's `.claude/settings.json`, and copy the folders in `skills/` into `.claude/skills/`.

## Set up a project

Put a `.patient-info.json` in the project root (see [examples/patient-info.json](examples/patient-info.json)). The hook stays silent for files not listed there.

```json
{
  "files": [{ "glob": "leaflet/en/*.html", "lang": "en" }, { "glob": "leaflet/ja/*.html", "lang": "ja" }],
  "pairs": [["leaflet/en/index.html", "leaflet/ja/index.html"]],
  "ignore_selectors": ["sup.cite", ".references"],
  "address_reader": "you",
  "jargon_allow": ["CT"]
}
```

Files can be HTML, Markdown or plain text. `"lang": "auto"` checks each paragraph by whether it contains kana, for files that hold both languages.

## Use

- Ask Claude: "Review leaflet/en/index.html for patients" (uses the `patient-info-review` skill), or name a skill: "Score this with PEMAT", "Rewrite this in やさしい日本語".
- Command line: `pitk check` (all configured files) or `pitk check file.html --json`. Add `--scores` to print every readability score. Exit code 1 if there are errors, so it can run in CI.
- `pitk contrast style.css`: contrast of every CSS rule that sets both a text and a background colour.
- `pitk cvd figure.png`: writes `figure-cvd.png`, the picture as seen with protanopia, deuteranopia and tritanopia (needs `numpy` and `Pillow`).
- `pitk panel results.json` and `pitk agree run1.json run2.json run3.json`: add up the AI reader panel and repeated scorings (see the skills below).

## Skills

| Skill | What it does |
| --- | --- |
| `patient-info-review` | Runs the checker, then the right reviews, then a table of suggested edits; PIF TICK process check |
| `pemat-review` | PEMAT-P / PEMAT-A/V scoring (understandability, actionability) |
| `clear-communication-index` | CDC Clear Communication Index (target 90+) |
| `dental-consent-content` | What dental and oral surgery materials should cover: material risks with numbers, alternatives including no treatment, risks of waiting, risk factors, next step (RCS 2020, ADA 2020, JP 2019) |
| `ai-reader-panel` | Simulated user test: 20 independent AI readers with different backgrounds answer key-message questions, a judge marks them, scored against the MHRA 16-of-20 benchmark. A pre-test only |
| `scoring-reliability` | PEMAT or CDC scoring run 3+ times independently; mean, SD, item agreement and Fleiss' kappa |
| `risk-communication` | Natural frequencies, same denominator, absolute risk, uncertainty (IPDAS, NHS) |
| `plain-language-rewrite` | English rewrite: you, active voice, ≤ 20 words, plain word first (NHS, ISO 24495-1) |
| `yasashii-nihongo` | Japanese rewrite in やさしい日本語 with a kanji limit |
| `cross-format-consistency` | Same facts and numbers across leaflet, web, script and translation |

## Tests

```
python3 -m unittest discover tests
```

## Licence

Code and skills: MIT (see LICENSE). The kanji lists in `pitk/data/` are derived from KANJIDIC2 (© EDRDG, CC BY-SA 4.0). PEMAT, the CDC Clear Communication Index and the other guidelines belong to their publishers; the skills summarise them and link to the originals.

Made for the Wisdom Tooth Education Models Study, Nagoya University. Contributions welcome.
