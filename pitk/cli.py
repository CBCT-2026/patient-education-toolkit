"""Command line and Claude Code hook entry points.

  python3 -m pitk check [FILE ...] [--lang en|ja] [--json] [--scores]   check files (default: every file in .patient-info.json)
  python3 -m pitk hook                                      PostToolUse hook: reads the hook JSON on stdin

Exit code of `check`: 1 if any finding is an error, else 0.
"""
import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

from . import checks, config, extract


def file_lang(root, path, cfg):
    rel = os.path.relpath(Path(path).resolve(), root) if root else str(path)
    for f in cfg['files']:
        if fnmatch.fnmatch(rel, f['glob']):
            return f.get('lang', 'auto')
    return None


KANA = re.compile(r'[\u3040-\u30ff]')


def split_lang(doc):
    """For a file holding both languages: one Doc per language, by whether each unit has kana."""
    out = {}
    for lg in ('en', 'ja'):
        secs = [extract.Section(s.title, [u for u in s.units if bool(KANA.search(u)) == (lg == 'ja')]) for s in doc.sections]
        out[lg] = extract.Doc(doc.path, [s for s in secs if s.units], doc.images, doc.links, doc.headings)
    return out


def check_file(path, lang, cfg, scores=None):
    doc = extract.load(path, cfg.get('ignore_selectors', []))
    skip = [re.compile(x, re.I) for x in cfg.get('ignore_sections', [])]
    doc.sections = [s for s in doc.sections if not any(x.search(s.title) for x in skip)]
    ck = checks.Checker(cfg)
    docs = split_lang(doc) if lang == 'auto' else {lang: doc}
    for lg, d in docs.items():
        if d.sections:
            ck.common(d, lg)
            (ck.japanese if lg == 'ja' else ck.english)(d)
    if scores is not None:
        scores += ck.scores
    return ck.out


def check_pairs(root, paths, cfg):
    out = []
    done = {str(Path(p).resolve()) for p in paths}
    for a, b in cfg['pairs']:
        pa, pb = (Path(root) / a).resolve(), (Path(root) / b).resolve()
        if (str(pa) in done or str(pb) in done) and pa.exists() and pb.exists():
            ign = cfg.get('ignore_selectors', [])
            out += checks.compare_pair(extract.load(pa, ign), extract.load(pb, ign), cfg)
    return out


def run(paths, root, cfg, lang=None, scores=None):
    findings = []
    for p in paths:
        lg = lang or file_lang(root, p, cfg) or 'auto'
        findings += check_file(p, lg, cfg, scores)
    findings += check_pairs(root, paths, cfg)
    return findings


def report(findings, root):
    lines = []
    for f in sorted(findings, key=lambda f: (f.file, f.severity != 'error', f.section)):
        lines.append(f'{os.path.relpath(f.file, root) if root else f.file}: {f.line()}')
    e = sum(f.severity == 'error' for f in findings)
    lines.append(f'{e} error(s), {len(findings) - e} warning(s).')
    return '\n'.join(lines)


def score_table(scores, root):
    """Readability scores per file and language. FKGL, SMOG, Fog, CLI, ARI are US school grades (lower is easier);
    Flesch Reading Ease 0-100 and jReadability 0.5-6.4 are higher-is-easier."""
    from .readability import EN
    lines = ['Readability (whole file):']
    for path, lang, sc in scores:
        name = os.path.relpath(path, root) if root else path
        if 'note' in sc:
            lines.append(f'  {name} [{lang}] {sc["note"]}')
        elif lang == 'en':
            vals = ', '.join(f'{label} {"n/a (<3 sentences)" if sc[k] is None else sc[k]}' for k, (label, _, _) in EN.items())
            lines.append(f'  {name} [en] {sc["words"]} words, {sc["sentences"]} sentences: {vals}')
        else:
            lines.append(f'  {name} [ja] jReadability {sc["jread"]} ({sc["level"]}); {sc["sentences"]} sentences, '
                         f'{sc["mean_sentence_words"]} words per sentence, kango {sc["kango_pct"]}%, wago {sc["wago_pct"]}%, '
                         f'verbs {sc["verb_pct"]}%, particles {sc["particle_pct"]}%')
    return '\n'.join(lines)


def cmd_check(args):
    root = config.find_root(Path(args.files[0]).parent if args.files else Path.cwd()) or Path.cwd()
    cfg = config.load(root)
    paths = args.files or sorted({str(p) for f in cfg['files'] for p in Path(root).glob(f['glob'])})
    if not paths:
        print('No files to check. List them in .patient-info.json ("files") or pass them on the command line.')
        return 0
    scores = []
    findings = run(paths, root, cfg, args.lang, scores)
    if args.json:
        out = [f.__dict__ for f in findings]
        if args.scores:
            out = {'findings': out, 'scores': [{'file': p, 'lang': lg, **sc} for p, lg, sc in scores]}
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        print(report(findings, root))
        if args.scores:
            print(score_table(scores, root))
    return 1 if any(f.severity == 'error' for f in findings) else 0


def cmd_hook(_args):
    """PostToolUse hook for Write/Edit/MultiEdit. Silent unless the edited file is listed in .patient-info.json.
    Errors go back to Claude as a block decision (Claude must fix them); warnings as extra context."""
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get('tool_input') or {}).get('file_path')
    if not path or not Path(path).exists():
        return 0
    root = config.find_root(os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or Path(path).parent)
    if not root:
        return 0
    cfg = config.load(root)
    lang = file_lang(root, path, cfg)
    if not lang:
        return 0
    try:
        findings = run([path], root, cfg, lang)
    except ImportError as e:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext':
              f'patient-education-toolkit could not run ({e}). Install: pip install beautifulsoup4 textstat==0.7.3'}}))
        return 0
    if not findings:
        return 0
    text = 'Patient information checks (patient-education-toolkit):\n' + report(findings, root)
    if any(f.severity == 'error' for f in findings):
        print(json.dumps({'decision': 'block', 'reason': text + '\nFix the errors, or explain to the user why a rule '
                          'should be relaxed in .patient-info.json.'}, ensure_ascii=False))
    else:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': text}},
                         ensure_ascii=False))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='pitk', description='Deterministic checks for patient information documents.')
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('check', help='check files')
    c.add_argument('files', nargs='*')
    c.add_argument('--lang', choices=['en', 'ja', 'auto'])
    c.add_argument('--json', action='store_true')
    c.add_argument('--scores', action='store_true', help='also print all readability scores')
    sub.add_parser('hook', help='Claude Code PostToolUse hook (reads stdin)')
    args = ap.parse_args(argv)
    return {'check': cmd_check, 'hook': cmd_hook}[args.cmd](args)
