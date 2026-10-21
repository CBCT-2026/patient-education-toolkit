"""Checks for spoken scripts, subtitles, labels and colour. Sources: docs/guidelines.md ("Video, narration and colour").

  spoken length   words / words per minute (EN) or characters / characters per second (JA) against a time limit
  subtitles       line length, reading speed and cue duration (Netflix timed text style guides; BBC subtitle guidelines)
  labels          two label sets (e.g. video and web page) must use the same names
  contrast        WCAG 2.2 contrast ratio for colour pairs and simple CSS rules
  colour vision   pitk cvd: simulated protanopia, deuteranopia and tritanopia (Machado, Oliveira & Fernandes 2009)
"""
import fnmatch
import json
import os
import re
from pathlib import Path

from .checks import Finding

KANA = re.compile(r'[぀-ヿ]')
SUB = {  # max characters per line, max characters per second, min and max seconds per cue
    'en': (42, 20, 5 / 6, 7),
    'ja': (16, 4, 5 / 6, 7),
}


def _f(cfg, rule, path, section, message, excerpt=''):
    sev = cfg['severity'].get(rule, 'warn')
    return [] if sev == 'off' else [Finding(rule, sev, str(path), section, message, excerpt)]


def _rel(root, p):
    return os.path.relpath(Path(p).resolve(), root) if root else str(p)


def matches(root, path, pattern):
    return fnmatch.fnmatch(_rel(root, path), pattern)


def media_files(root, cfg):
    """Files named in the spoken, subtitles and label_sets settings."""
    out = set()
    for e in cfg.get('spoken', []) + cfg.get('subtitles', []):
        out |= {str(p) for p in Path(root).glob(e['glob'])}
    for e in cfg.get('label_sets', []):
        if (Path(root) / e['file']).exists():
            out.add(str(Path(root) / e['file']))
    return out


# ---------- spoken scripts ----------
def spoken_seconds(text, lang, cfg):
    if lang == 'ja':
        return len(re.sub(r'[\s「」（）・]', '', text)) / cfg['ja_chars_per_second']
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text)) / cfg['en_words_per_minute'] * 60


def check_spoken(root, path, cfg, doc):
    out = []
    for e in cfg.get('spoken', []):
        if not matches(root, path, e['glob']):
            continue
        rx = re.compile(e['sections']) if e.get('sections') else None
        by_lang = {}
        for s in doc.sections:
            if rx and not rx.search(s.title):
                continue
            for u in s.units[1:] if rx else s.units:  # the heading itself is not spoken
                lg = 'ja' if KANA.search(u) else 'en'
                by_lang.setdefault(lg, []).append(u)
        for lg, units in by_lang.items():
            secs = spoken_seconds(' '.join(units), lg, cfg)
            rate = f'{cfg["en_words_per_minute"]} words a minute' if lg == 'en' else f'{cfg["ja_chars_per_second"]} characters a second'
            if secs > e['max_seconds']:
                out += _f(cfg, 'spoken-length', path, f'(spoken, {lg})', f'About {secs:.0f} s at {rate}, over '
                          f'{e["max_seconds"]} s. Cut words, or measure the real recording.')
    return out


# ---------- subtitles ----------
def _t(s):
    h, m, rest = ([0] + s.replace(',', '.').split(':'))[-3:]
    return int(h) * 3600 + int(m) * 60 + float(rest)


def cues(text):
    """(start, end, [lines]) for each cue in a WebVTT or SRT file."""
    out = []
    for block in re.split(r'\n\s*\n', text.replace('\r', '')):
        lines = block.strip().split('\n')
        for i, l in enumerate(lines):
            m = re.match(r'([\d:.,]+)\s*-->\s*([\d:.,]+)', l)
            if m:
                txt = [re.sub(r'<[^>]+>', '', x) for x in lines[i + 1:] if x.strip()]
                out.append((_t(m.group(1)), _t(m.group(2)), txt))
                break
    return out


def check_subtitles(root, path, cfg):
    out = []
    for e in cfg.get('subtitles', []):
        if not matches(root, path, e['glob']):
            continue
        lg = e.get('lang', 'en')
        max_line, max_cps, min_s, max_s = SUB[lg]
        max_line, max_cps = e.get('max_line', max_line), e.get('max_cps', max_cps)
        for start, end, lines in cues(Path(path).read_text(encoding='utf-8')):
            text = ' '.join(lines)
            sec = f'{start:.1f} s'
            for l in lines:
                if len(l) > max_line:
                    out += _f(cfg, 'sub-line-length', path, sec, f'Line of {len(l)} characters (aim for {max_line} or '
                              'fewer; split it into 2 lines).', l[:60])
            if len(lines) > 2:
                out += _f(cfg, 'sub-line-length', path, sec, f'{len(lines)} lines in one subtitle (2 at most).', text[:60])
            dur = end - start
            chars = len(text.replace(' ', '')) if lg == 'ja' else len(text)
            if dur > 0 and chars / dur > max_cps:
                out += _f(cfg, 'sub-reading-speed', path, sec, f'{chars / dur:.0f} characters a second (aim for '
                          f'{max_cps} or fewer): show it for longer or use fewer words.', text[:60])
            if dur < min_s or dur > max_s:
                out += _f(cfg, 'sub-duration', path, sec, f'On screen for {dur:.1f} s (aim for {min_s:.2f} to {max_s} s).',
                          text[:60])
    return out


# ---------- labels ----------
def label_set(root, e):
    p = Path(root) / e['file']
    if 'json' in e:
        d = json.loads(p.read_text(encoding='utf-8'))
        for k in e['json'].split('.'):
            d = d[k]
        vals = d.values() if isinstance(d, dict) else d
        return {(v[0] if isinstance(v, list) else v).strip() for v in vals}
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
    names = set()
    for el in soup.select(e['selector']):
        for small in el.find_all(['small', 'sub']):
            small.decompose()  # the medical name under the main label
        names.add(' '.join(el.get_text(' ').split()))
    return names


def check_labels(root, path, cfg):
    sets = cfg.get('label_sets', [])
    if len(sets) < 2 or (path and not any(matches(root, path, e['file']) for e in sets)):
        return []
    out = []
    base = label_set(root, sets[0])
    for e in sets[1:]:
        other = label_set(root, e)
        lo = lambda s: {x.lower() for x in s}
        a, b = lo(base) - lo(other), lo(other) - lo(base)
        if a or b:
            out += _f(cfg, 'labels-differ', Path(root) / e['file'], '(labels)', f'Labels differ from {sets[0]["file"]}: '
                      f'only there {sorted(a) or "-"}; only here {sorted(b) or "-"}.')
    return out


# ---------- colour ----------
def parse_colour(s):
    s = s.strip().lower()
    named = {'white': '#ffffff', 'black': '#000000'}
    s = named.get(s, s)
    m = re.fullmatch(r'#([0-9a-f]{3}|[0-9a-f]{6})', s)
    if m:
        h = m.group(1)
        h = ''.join(c * 2 for c in h) if len(h) == 3 else h
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r'rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+%?))?\s*\)', s)
    if m and (m.group(4) is None or m.group(4) in ('1', '100%')):
        return tuple(int(m.group(i)) for i in (1, 2, 3))
    return None


def luminance(rgb):
    c = [x / 255 for x in rgb]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted([luminance(a), luminance(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_colour_pairs(cfg, where):
    out = []
    for fg, bg, *rest in cfg.get('colour_pairs', []):
        large = 'large' in rest
        name = ' '.join(x for x in rest if x != 'large') or fg
        need = 3 if large else 4.5
        r = contrast(parse_colour(fg), parse_colour(bg))
        if r < need:
            out += _f(cfg, 'contrast', where, '(colours)', f'{name}: {fg} on {bg} has contrast {r:.1f}:1, below {need}:1 '
                      '(WCAG 2.2: 4.5:1 for normal text; 3:1 for large text, 24 px, or bold text of 18.7 px and up).')
    return out


def css_pairs(text):
    """(selector, colour, background) for CSS rules that set both, after resolving simple custom properties."""
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    var = dict(re.findall(r'(--[\w-]+)\s*:\s*([^;}]+)', text))
    res = lambda v: re.sub(r'var\((--[\w-]+)(?:,\s*([^)]+))?\)', lambda m: var.get(m.group(1), m.group(2) or ''), v).strip()
    out = []
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*)\}', text):
        d = dict((k.strip().lower(), res(v)) for k, v in re.findall(r'([\w-]+)\s*:\s*([^;]+)', body))
        fg, bg = d.get('color'), d.get('background-color') or d.get('background')
        if fg and bg and parse_colour(fg) and parse_colour(bg.split()[0]):
            out.append((' '.join(sel.split()), fg, bg.split()[0]))
    return out


def contrast_report(paths):
    lines = []
    for p in paths:
        for sel, fg, bg in css_pairs(Path(p).read_text(encoding='utf-8')):
            r = contrast(parse_colour(fg), parse_colour(bg))
            flag = 'FAIL' if r < 3 else 'large text only' if r < 4.5 else 'ok'
            lines.append(f'{p}: {sel} | {fg} on {bg} | {r:.1f}:1 | {flag}')
    return lines


# Machado GM, Oliveira MM, Fernandes LAF (2009), severity 1.0, applied to linear RGB.
CVD = {
    'protanopia': [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    'deuteranopia': [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    'tritanopia': [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}


def simulate(path, out_dir=None):
    """Write <name>-cvd.png: the original and the 3 simulations side by side, each labelled."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(float) / 255
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    tiles = [('original', im)]
    for name, m in CVD.items():
        s = np.clip(lin @ np.array(m).T, 0, 1)
        srgb = np.where(s <= 0.0031308, s * 12.92, 1.055 * s ** (1 / 2.4) - 0.055)
        tiles.append((name, Image.fromarray((srgb * 255).round().astype('uint8'))))
    w, h = im.size
    pad = max(40, h // 16)
    try:
        font = ImageFont.load_default(size=pad * 3 // 5)
    except TypeError:  # Pillow before 10.1
        font = ImageFont.load_default()
    sheet = Image.new('RGB', (w * 2, (h + pad) * 2), 'white')
    for i, (name, t) in enumerate(tiles):
        x, y = (i % 2) * w, (i // 2) * (h + pad)
        sheet.paste(t, (x, y + pad))
        ImageDraw.Draw(sheet).text((x + 10, y + pad // 6), name, fill='black', font=font)
    out = Path(out_dir or Path(path).parent) / (Path(path).stem + '-cvd.png')
    sheet.save(out)
    return out
