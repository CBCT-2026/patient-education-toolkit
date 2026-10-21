"""Turn a patient information file (HTML, Markdown or plain text) into sections of text units.

A unit is one heading, paragraph, list item, table cell or caption: the smallest piece a reader sees on its own.
Units are scored as sentences, so a short bullet is not merged into the next one.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

BLOCKS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th', 'dt', 'dd', 'figcaption', 'caption', 'blockquote']
CONTAINERS = ['p', 'li', 'ul', 'ol', 'table', 'figcaption', 'dl', 'blockquote', 'div', 'section']


@dataclass
class Section:
    title: str
    units: list = field(default_factory=list)


@dataclass
class Doc:
    path: str
    sections: list
    images: list = field(default_factory=list)   # (src, alt or None)
    links: list = field(default_factory=list)    # link texts
    headings: list = field(default_factory=list)  # (level, text)

    @property
    def units(self):
        return [u for s in self.sections for u in s.units]

    @property
    def text(self):
        return '\n'.join(self.units)


def _norm(s):
    return ' '.join(s.split())


def from_html(path, text, ignore=()):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    for sel in ['script', 'style', 'noscript', 'template', *ignore]:
        for x in soup.select(sel):
            x.decompose()
    root = soup.find('main') or soup.body or soup
    images = [(i.get('src', ''), i.get('alt')) for i in root.find_all('img')]
    links = [_norm(a.get_text(' ')) for a in root.find_all('a')]
    sections = [Section('(start)')]
    headings = []
    for el in root.find_all(BLOCKS):
        if el.name not in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') and el.find(CONTAINERS):
            continue  # a wrapper; its children are units of their own
        t = _norm(el.get_text(' '))
        if not t:
            continue
        if el.name in ('h1', 'h2'):
            sections.append(Section(t))
        if el.name[0] == 'h' and el.name[1:].isdigit():
            headings.append((int(el.name[1]), t))
        sections[-1].units.append(t)
    return Doc(path, [s for s in sections if s.units], images, links, headings)


MD_IMG = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)[^)]*\)')
MD_LINK = re.compile(r'\[([^\]]+)\]\([^)]+\)')


def from_markdown(path, text):
    sections = [Section('(start)')]
    images, links, headings = [], [], []
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        if in_code or not line.strip() or re.match(r'^\s*(---+|\|?\s*:?-+)', line) or line.lstrip().startswith('<!--'):
            continue
        for alt, src in MD_IMG.findall(line):
            images.append((src, alt))
        line = MD_IMG.sub('', line)
        links += MD_LINK.findall(line)
        line = MD_LINK.sub(r'\1', line)
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        t = re.sub(r'[*_`>]+', '', re.sub(r'^\s*([-*+]|\d+[.)])\s+', '', m.group(2) if m else line))
        t = _norm(t.replace('|', ' '))
        if not t:
            continue
        if m:
            headings.append((len(m.group(1)), t))
            if len(m.group(1)) <= 2:
                sections.append(Section(t))
        sections[-1].units.append(t)
    return Doc(path, [s for s in sections if s.units], images, links, headings)


def load(path, ignore=()):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    if p.suffix.lower() in ('.html', '.htm'):
        return from_html(str(path), text, ignore)
    return from_markdown(str(path), text)
