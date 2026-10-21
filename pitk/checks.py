"""Deterministic checks for patient information text. Each returns a list of Finding.

Sources for the thresholds are listed in docs/guidelines.md.
"""
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parent / 'data'


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    section: str
    message: str
    excerpt: str = ''

    def line(self):
        ex = f' | "{self.excerpt}"' if self.excerpt else ''
        return f'[{self.severity}] {self.rule} | {self.section} | {self.message}{ex}'


def _kanji(name):
    lines = (DATA / f'{name}_kanji{"_2020" if name == "kyouiku" else ""}.txt').read_text(encoding='utf-8').splitlines()
    return set(''.join(l for l in lines if not l.startswith('#')))


def _jargon(lang, cfg):
    d = json.loads((DATA / f'jargon_{lang}.json').read_text(encoding='utf-8'))
    d.pop('_note', None)
    d.update(cfg.get('jargon_extra', {}).get(lang, {}))
    allow = {a.lower() for a in cfg.get('jargon_allow', [])}
    return {k: v for k, v in d.items() if k.lower() not in allow}


def _cut(s, start, end, pad=30):
    return ('…' if start > pad else '') + s[max(0, start - pad):end + pad].strip() + ('…' if end + pad < len(s) else '')


# Citation markers: [1], [1-3], and template keys like [[smith]] or {{credit:fig1}}
CITE = re.compile(r'\[\d+(?:\s*[,–-]\s*\d+)*\]|\[\[[\w:.-]+\]\]|\{\{[^}]*\}\}')
# A term counts as explained where it is introduced: in brackets, or after "name is" / "called" / 「…」と言います.
DEFINED = re.compile(r'((medical|other|full|proper|technical) name (is|for)|called|known as|means)\s+(the\s+|an?\s+)?([\w-]+\s+){0,3}$', re.I)


def _explained(u, m):
    before, after = u[:m.start()], u[m.end():]
    if before.rstrip().endswith(('(', '（', '「')) and after.lstrip()[:1] in (')', '）', '」'):
        return True
    return bool(DEFINED.search(before[-40:])) or bool(re.match(r'\s*」?\s*(と(言|い)います|と呼びます)', after))



class Checker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.out = []

    def add(self, rule, doc, section, message, excerpt=''):
        sev = self.cfg['severity'].get(rule, 'warn')
        if sev != 'off':
            self.out.append(Finding(rule, sev, doc.path, section, message, excerpt))

    # ---------- shared ----------
    def common(self, doc, lang):
        for src, alt in doc.images:
            if alt is None:
                self.add('img-alt', doc, '(images)', f'Image has no alt text: {src}')
        bad = {'click here', 'here', 'more', 'read more', 'link', 'this link', 'こちら', 'ここ', 'こちらをクリック'}
        for t in doc.links:
            if t.strip().lower() in bad:
                self.add('link-text', doc, '(links)', f'Link text "{t}" does not say where it goes.')
        req = self.cfg.get('require', {})
        raw = Path(doc.path).read_text(encoding='utf-8') if req and Path(doc.path).exists() else ''
        for label, rx in req.items():
            if not re.search(rx, raw):
                self.add('require', doc, '(whole file)', f'Missing: {label} (pattern {rx}).')
        jar = _jargon(lang, self.cfg)
        for s in doc.sections:
            for u in s.units:
                u = CITE.sub('', u)
                for term, plain in jar.items():
                    if lang == 'ja':
                        m = re.search(re.escape(term), u)
                    elif term.isupper():
                        m = re.search(r'\b' + re.escape(term) + r's?\b', u)
                    else:
                        m = re.search(r'\b' + re.escape(term) + r'\b', u, re.I)
                    if m and not _explained(u, m):
                        self.add('jargon', doc, s.title, f'"{m.group(0)}": try "{plain}", or explain it and add to jargon_allow.',
                                 _cut(u, m.start(), m.end()))
                for m in re.finditer(r'\d+(?:\.\d+)?\s?(%|％|percent|per cent|パーセント)', u):
                    self.add('percent', doc, s.title, 'Percentage: give risk as "X in 100" (natural frequency).',
                             _cut(u, m.start(), m.end()))

    # ---------- English ----------
    def english(self, doc):
        import textstat
        cfg = self.cfg
        for s in doc.sections:
            units = [CITE.sub('', u).strip() for u in s.units]
            text = ' '.join(u if u[-1:] in '.?!:' else u + '.' for u in units if u)
            if len(text.split()) >= 10:
                g = textstat.flesch_kincaid_grade(text)
                if g > cfg['en_max_fkgl']:
                    self.add('en-fkgl', doc, s.title, f'Reading grade (FKGL) {g:.1f}, above {cfg["en_max_fkgl"]}. '
                             'Use shorter sentences and shorter words.')
            for u in units:
                for sent in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"“(])', u):
                    n = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", sent))
                    if n > cfg['en_max_sentence_words']:
                        self.add('en-sentence-length', doc, s.title, f'{n} words in one sentence (aim for '
                                 f'{cfg["en_max_sentence_words"]} or fewer).', sent[:90] + ('…' if len(sent) > 90 else ''))
                self._en_unit(doc, s.title, u)
        self._en_doc(doc)

    PASSIVE_OK = {'tired', 'worried', 'interested', 'used', 'based', 'called', 'concerned', 'located', 'scared',
                  'supposed', 'pleased', 'prepared', 'involved', 'married', 'needed', 'allowed', 'red', 'bored',
                  'surprised', 'excited', 'shed', 'bed', 'seed', 'feed', 'need', 'speed', 'linked', 'related', 'numbed',
                  'asked', 'advised', 'limited', 'closed', 'stuck', 'born', 'open', 'even', 'often', 'seven', 'eleven',
                  'given', 'when', 'then', 'ten', 'men', 'women', 'children', 'hidden', 'swollen', 'golden', 'broken'}
    PASSIVE = re.compile(r"\b(am|is|are|was|were|be|been|being|get|gets|got)\s+(?:\w+ly\s+)?(\w+(?:ed|en)|done|made|"
                         r"seen|taken|shown|known|told|found|put|cut|hurt|felt|held|kept|left|lost|paid|sent|set|built|"
                         r"brought|caught|taught|thought)\b", re.I)

    def _en_unit(self, doc, sec, u):
        mode = self.cfg['address_reader']
        if mode == 'neutral':
            for m in re.finditer(r"\b(you|your|yours|yourself|you're|you'll)\b", u, re.I):
                self.add('address-neutral', doc, sec, f'"{m.group(0)}": this project uses neutral wording.',
                         _cut(u, m.start(), m.end()))
        elif mode == 'you':
            for m in re.finditer(r'\b(the patient|patients|the person|a person|people who|the reader|the individual|'
                                 r'one should|anyone who|someone who)\b', u, re.I):
                self.add('address-you', doc, sec, f'"{m.group(0)}": speak to the reader as "you" (NHS, CDC).',
                         _cut(u, m.start(), m.end()))
        for m in self.PASSIVE.finditer(u):
            if m.group(2).lower() not in self.PASSIVE_OK:
                self.add('passive-voice', doc, sec, f'Possible passive voice "{m.group(0)}": say who does what.',
                         _cut(u, m.start(), m.end()))
        if not re.search(r'\d', u):
            m = re.search(r'\b(rare|rarely|uncommon|very common|common|small risk|low risk|high risk|frequently|'
                          r'infrequently|occasionally)\b', u, re.I)
            if m:
                self.add('verbal-risk', doc, sec, f'"{m.group(0)}" without a number: if this is a risk, add '
                         '"about X in 100".', _cut(u, m.start(), m.end()))
        m = re.search(r'\b(times (more|less) likely|twice as likely|half as likely|(increases|reduces|lowers|raises|halves|'
                      r'doubles) (the |your )?(risk|chance)( by)?)\b', u, re.I)
        if m:
            self.add('relative-risk', doc, sec, 'Relative risk: also give the absolute numbers ("from X in 100 to '
                     'Y in 100").', _cut(u, m.start(), m.end()))
        for m in re.finditer(r'\b(?:[A-Z]{3,}\s+){1,}[A-Z]{3,}\b', u):
            self.add('all-caps', doc, sec, 'Words in capitals are harder to read: use bold instead.',
                     _cut(u, m.start(), m.end()))
        for m in re.finditer(r"\b(not|n't|never)\s+(un\w+|impossible|without|uncommon|unlikely)\b", u, re.I):
            self.add('double-negative', doc, sec, f'Double negative "{m.group(0)}": say it positively.',
                     _cut(u, m.start(), m.end()))

    COMMON_ACRONYMS = {'NHS', 'UK', 'US', 'USA', 'OK', 'TV', 'PhD', 'DNA', 'GP', 'PDF', 'QR', 'ID', 'EU', 'WHO', 'CDC',
                       'AM', 'PM', 'FAQ', 'URL', 'BMJ'}

    def _en_doc(self, doc):
        text = doc.text
        jar = {k for k in _jargon('en', self.cfg) if k.isupper()}
        allow = set(self.cfg.get('jargon_allow', [])) | self.COMMON_ACRONYMS
        seen = set()
        for s in doc.sections:
            for u in s.units:
                for m in re.finditer(r'\b([A-Z]{2,6})s?\b', u):
                    a = m.group(1)
                    if a in seen or a in allow or a in jar:
                        continue
                    seen.add(a)
                    if not re.search(r'\(\s*' + a + r's?\s*\)|\b' + a + r's?\s*\(', text):
                        self.add('acronym', doc, s.title, f'"{a}" is not spelled out the first time.',
                                 _cut(u, m.start(), m.end()))
        if self.cfg['address_reader'] == 'you' and len(doc.units) > 5 and \
                not re.search(r"\b(you|your)\b", text, re.I):
            self.add('address-you', doc, '(whole file)', 'The text never says "you". NHS and CDC guidance: speak to the reader.')
        self._denominators(doc)

    def _denominators(self, doc):
        dens = Counter()
        for u in doc.units:
            t = unicodedata.normalize('NFKC', u)
            for m in re.finditer(r'\b\d[\d,]*\s+(?:in|out of)\s+(\d[\d,]*)\b', t):
                dens[m.group(1).replace(',', '')] += 1
            for m in re.finditer(r'(\d[\d,]*)人(?:に|中|のうち)\s*\d', t):
                dens[m.group(1).replace(',', '')] += 1
        if len(dens) > 1:
            self.add('mixed-denominators', doc, '(whole file)', 'Risks use different denominators (' +
                     ', '.join(f'"in {d}"' for d in dens) + '). Use the same one, e.g. "X in 100".')

    # ---------- Japanese ----------
    def japanese(self, doc):
        cfg = self.cfg
        allowed = _kanji(cfg['ja_kanji']) if cfg.get('ja_kanji') else None
        label = {'kyouiku': '小学校で習う漢字（教育漢字）', 'jouyou': '常用漢字'}.get(cfg.get('ja_kanji'), '')
        for s in doc.sections:
            chars = kanji = 0
            for u in s.units:
                u = CITE.sub('', u)
                if allowed is not None:
                    bad = sorted({c for c in u if '一' <= c <= '鿿' and c not in allowed}, key=u.index)
                    if bad:
                        i = u.index(bad[0])
                        self.add('ja-kanji', doc, s.title, f'{label}以外の漢字: {"".join(bad)}（ひらがなにするか、'
                                 '言いかえてください）', _cut(u, i, i + 1, 20))
                for sent in re.split(r'(?<=[。！？])', u):
                    n = len(re.sub(r'\s', '', sent))
                    if n > cfg['ja_max_sentence_chars']:
                        self.add('ja-sentence-length', doc, s.title, f'1文が{n}字（{cfg["ja_max_sentence_chars"]}字'
                                 '以下にしてください）', sent[:60] + ('…' if len(sent) > 60 else ''))
                body = re.sub(r'[\s\x00-\x7f。、・「」（）！？：；ー―…]', '', u)
                chars += len(body)
                kanji += sum('一' <= c <= '鿿' for c in body)
                m = re.search(r'(いただ[きくけいか]|ございま|おりま|申し|致し|させていただ|くださいませ)', u)
                if m:
                    self.add('ja-keigo', doc, s.title, f'敬語「{m.group(0)}」: やさしい日本語では「です・ます」で書きます。',
                             _cut(u, m.start(), m.end(), 20))
                m = re.search(r'(ないわけではない|なくはない|ないことはない|なくもない|ないとは限らない)', u)
                if m:
                    self.add('double-negative', doc, s.title, f'二重否定「{m.group(0)}」: 肯定の形で書いてください。',
                             _cut(u, m.start(), m.end(), 20))
                if cfg.get('ja_address_reader') == 'neutral' and 'あなた' in u:
                    i = u.index('あなた')
                    self.add('address-neutral', doc, s.title, '「あなた」: このプロジェクトでは使いません。', _cut(u, i, i + 3, 20))
            if chars >= 40 and kanji / chars > cfg['ja_max_kanji_ratio']:
                self.add('ja-kanji-ratio', doc, s.title, f'漢字の割合 {kanji / chars:.0%}（{cfg["ja_max_kanji_ratio"]:.0%}'
                         '以下が目安）。ひらがなを増やしてください。')
        self._denominators(doc)


WORDS = {w: str(i) for i, w in enumerate('two three four five six seven eight nine ten'.split(), 2)}


def _numbers(doc):
    t = unicodedata.normalize('NFKC', doc.text)
    t = CITE.sub('', t)
    t = re.sub(r'\b(' + '|'.join(WORDS) + r')\b', lambda m: WORDS[m.group(1).lower()], t, flags=re.I)
    return Counter(re.findall(r'\d+(?:\.\d+)?', t.replace(',', '')))


def _img_key(src):
    name = Path(src).name.lower()
    return re.sub(r'[-_](en|ja|jp)(?=\.)', '', name)


def compare_pair(a, b, cfg):
    """Two language versions of the same material must carry the same numbers, sections and pictures."""
    ck = Checker(cfg)
    na, nb = _numbers(a), _numbers(b)
    if na != nb:
        only_a, only_b = na - nb, nb - na
        ck.add('pair-numbers', a, '(pair)', f'Numbers differ from {Path(b.path).name}: only here '
               f'{dict(only_a) or "-"}; only there {dict(only_b) or "-"}.')
    ha = [h for lvl, h in a.headings if lvl <= 2]
    hb = [h for lvl, h in b.headings if lvl <= 2]
    if len(ha) != len(hb):
        ck.add('pair-sections', a, '(pair)', f'{len(ha)} main headings here, {len(hb)} in {Path(b.path).name}.')
    ia, ib = [_img_key(s) for s, _ in a.images], [_img_key(s) for s, _ in b.images]
    if ia != ib:
        ck.add('pair-images', a, '(pair)', f'Pictures differ from {Path(b.path).name}: {ia} vs {ib}.')
    return ck.out
