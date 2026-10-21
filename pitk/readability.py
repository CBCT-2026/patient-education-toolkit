"""Readability formulas. Citations and limits: docs/guidelines.md ("Readability formulas").

English scores come from textstat (pinned 0.7.3). The Japanese score is jReadability (Lee 2016; Hasebe & Lee 2015),
computed here from a UniDic morphological analysis (fugashi + unidic-lite, optional: without them it is skipped).
"""
import re

EN = {  # key: (label, textstat function, higher is easier)
    'fkgl': ('Flesch-Kincaid grade', 'flesch_kincaid_grade', False),
    'smog': ('SMOG grade', 'smog_index', False),
    'fre': ('Flesch Reading Ease', 'flesch_reading_ease', True),
    'fog': ('Gunning Fog', 'gunning_fog', False),
    'cli': ('Coleman-Liau', 'coleman_liau_index', False),
    'ari': ('Automated Readability Index', 'automated_readability_index', False),
}


def en_scores(text):
    """All English scores for one text. SMOG needs 3 or more sentences (it was built on samples of 30): None below that."""
    import textstat
    out = {k: round(getattr(textstat, fn)(text), 1) for k, (_, fn, _) in EN.items()}
    out['sentences'] = textstat.sentence_count(text)
    out['words'] = textstat.lexicon_count(text)
    if out['sentences'] < 3:
        out['smog'] = None
    return out


# jReadability levels (Hasebe & Lee 2015): higher score = easier text.
JA_LEVELS = [(5.5, '初級前半 lower elementary'), (4.5, '初級後半 upper elementary'), (3.5, '中級前半 lower intermediate'),
             (2.5, '中級後半 upper intermediate'), (1.5, '上級前半 lower advanced'), (0.5, '上級後半 upper advanced')]
JA_END = ('。', '？', '！', '．', '?', '!')

_tagger = None


def ja_level(score):
    for lo, name in JA_LEVELS:
        if score >= lo:
            return name
    return 'above upper advanced'


def ja_score(text):
    """jReadability: 11.724 - 0.056 x mean sentence length (words) - 0.126 x % kango - 0.042 x % wago
    - 0.145 x % verbs - 0.044 x % particles. Counting follows the open-source jreadability package (MIT):
    every UniDic token counts as a word, and verbs exclude 非自立可能 (the あり of あります).
    Returns None if fugashi or a UniDic dictionary is not installed."""
    global _tagger
    try:
        if _tagger is None:
            import fugashi
            _tagger = fugashi.Tagger()
    except (ImportError, RuntimeError):
        return None
    toks = [t for t in _tagger(text) if t.surface.strip()]
    if not toks:
        return None
    sents, n = 0, 0
    for t in toks:
        n += 1
        if t.surface in JA_END:
            sents, n = sents + 1, 0
    sents += n > 0
    f = [t.feature for t in toks]
    pct = lambda k: 100.0 * k / len(toks)
    kango = pct(sum(x.goshu == '漢' for x in f))
    wago = pct(sum(x.goshu == '和' for x in f))
    verbs = pct(sum(x.pos1 == '動詞' and x.pos2 != '非自立可能' for x in f))
    particles = pct(sum(x.pos1 == '助詞' for x in f))
    mls = len(toks) / sents
    score = 11.724 - 0.056 * mls - 0.126 * kango - 0.042 * wago - 0.145 * verbs - 0.044 * particles
    return {'jread': round(score, 2), 'level': ja_level(score), 'sentences': sents, 'words': len(toks),
            'mean_sentence_words': round(mls, 1), 'kango_pct': round(kango, 1), 'wago_pct': round(wago, 1),
            'verb_pct': round(verbs, 1), 'particle_pct': round(particles, 1)}


def join_units(units, lang):
    """Join block elements into running text, ending each with a full stop so headings and list items count as sentences."""
    end = '.?!:' if lang == 'en' else ''.join(JA_END)
    stop = '.' if lang == 'en' else '。'
    units = [re.sub(r'\s+', ' ', u).strip() for u in units]
    return (' ' if lang == 'en' else '').join(u if u[-1:] in end else u + stop for u in units if u)
