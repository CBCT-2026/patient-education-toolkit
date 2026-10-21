"""Project settings, read from .patient-info.json at the project root (all keys optional)."""
import json
from pathlib import Path

NAME = '.patient-info.json'

DEFAULTS = {
    # Files to check: glob (relative to the project root) and language ("en", "ja", or "auto" for a file
    # holding both: each paragraph is checked by whether it contains kana). Default "auto".
    'files': [],
    # Pairs of files that must say the same thing in two languages: [["a-en.html", "a-ja.html"], ...]
    'pairs': [],
    # CSS selectors to leave out of HTML before checking (citations, credits, reference lists).
    'ignore_selectors': [],
    # Regexes for section headings to skip (notes for staff, reference lists).
    'ignore_sections': [],
    # "you": speak to the reader (NHS, CDC). "neutral": no you/your. "any": no check.
    'address_reader': 'you',
    # Japanese: "omit" (no check; natural Japanese leaves the subject out), "neutral" (flag あなた).
    'ja_address_reader': 'omit',
    # Readability (docs/guidelines.md, "Readability formulas"). FKGL per section; SMOG and Flesch Reading Ease on the
    # whole file. Gunning Fog, Coleman-Liau and ARI are reported only (pitk check --scores).
    'en_max_fkgl': 6,
    'en_max_smog': 6,
    'en_min_fre': 70,
    # jReadability (Japanese, higher = easier): warn below this. 3.5 = lower intermediate (中級前半) or easier.
    # Needs fugashi + unidic-lite; skipped if they are not installed.
    'ja_min_jread': 3.5,
    'en_max_sentence_words': 20,
    'ja_max_sentence_chars': 50,
    # "kyouiku" (grade 1-6 kanji, MEXT 2020), "jouyou" (2,136 jouyou kanji) or null (no check).
    'ja_kanji': 'kyouiku',
    'ja_max_kanji_ratio': 0.35,
    # Terms that are fine here (for example defined once on the page): ["AR", "CBCT"]
    'jargon_allow': [],
    # Extra project terms: {"en": {"term": "plain word"}, "ja": {...}}
    'jargon_extra': {'en': {}, 'ja': {}},
    # Text that must appear somewhere in each file (PIF TICK basics): {"date": "Published|作成日"}
    'require': {},
    # Claim map: every risk number in the files must be listed here, with the sources that support it.
    # [{"value": "7 in 100", "also": ["100人中約7人"], "cite": ["rico", "derbishi"], "note": "high-risk teeth"}]
    'claims': [],
    # Text colours to check for contrast (WCAG 2.2: 4.5 normal text, 3 large text). Add "large" for large or bold text:
    # [["#E46C0A", "#FFFFFF", "video name"], ["#1F7FB8", "#FFFFFF", "heading", "large"]]
    'colour_pairs': [],
    # Spoken scripts: estimated length must fit. [{"glob": "script.md", "max_seconds": 45, "sections": "^English$"}]
    'spoken': [],
    'en_words_per_minute': 150,
    'ja_chars_per_second': 5.5,
    # Subtitle files (.vtt, .srt): [{"glob": "video/en/*.vtt", "lang": "en"}]
    'subtitles': [],
    # Label sets that must use the same names, e.g. on-screen video labels vs web page labels:
    # [{"file": "video/script-en.json", "json": "labels"}, {"file": "en/index.html", "selector": ".label"}]
    'label_sets': [],
    # Per-rule severity: "error" (blocks in the hook), "warn" or "off".
    'severity': {},
}

SEVERITY = {
    'en-fkgl': 'error', 'en-smog': 'error', 'en-fre': 'warn', 'ja-jread': 'warn', 'en-sentence-length': 'warn', 'jargon': 'error', 'passive-voice': 'warn',
    'percent': 'warn', 'mixed-denominators': 'warn', 'verbal-risk': 'warn', 'relative-risk': 'warn',
    'address-you': 'warn', 'address-neutral': 'error', 'acronym': 'warn', 'all-caps': 'warn',
    'double-negative': 'warn', 'ja-kanji': 'error', 'ja-sentence-length': 'warn', 'ja-kanji-ratio': 'warn',
    'ja-keigo': 'warn', 'img-alt': 'error', 'link-text': 'warn', 'require': 'warn',
    'claim-unknown': 'error', 'claim-uncited': 'warn', 'img-alt-quality': 'warn', 'contrast': 'error',
    'spoken-length': 'error', 'sub-line-length': 'warn', 'sub-reading-speed': 'warn', 'sub-duration': 'warn',
    'labels-differ': 'warn',
    'pair-numbers': 'error', 'pair-sections': 'error', 'pair-images': 'error',
}


def find_root(start):
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        if (d / NAME).exists():
            return d
    return None


def load(root):
    cfg = json.loads(json.dumps(DEFAULTS))
    if root and (Path(root) / NAME).exists():
        cfg.update(json.loads((Path(root) / NAME).read_text(encoding='utf-8')))
    cfg['severity'] = {**SEVERITY, **cfg.get('severity', {})}
    return cfg
