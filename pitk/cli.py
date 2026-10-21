"""Command line and Claude Code hook entry points.

  python3 -m pitk check [FILE ...] [--lang en|ja] [--json] [--scores]   check files (default: every file in .patient-info.json)
  python3 -m pitk hook                                      PostToolUse hook: reads the hook JSON on stdin
  python3 -m pitk contrast FILE.css ...                     contrast of every CSS rule that sets text and background colour
  python3 -m pitk cvd IMAGE ...                             colour-blind previews (protanopia, deuteranopia, tritanopia)
  python3 -m pitk panel RESULTS.json                        tally a simulated reader panel (skill ai-reader-panel)
  python3 -m pitk agree RUN.json RUN.json ...               agreement between repeated PEMAT / CDC scorings

Exit code of `check`: 1 if any finding is an error, else 0.
"""
import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

from . import checks, config, extract, media, scoring


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


def run(paths, root, cfg, lang=None, scores=None, project=False):
    findings = []
    media_paths = {str(Path(p).resolve()) for p in media.media_files(root, cfg)} if root else set()
    for p in paths:
        lg = lang or file_lang(root, p, cfg)
        if lg or str(Path(p).resolve()) not in media_paths:
            findings += check_file(p, lg or 'auto', cfg, scores)
        if root:
            if Path(p).suffix.lower() in ('.vtt', '.srt'):
                findings += media.check_subtitles(root, p, cfg)
            elif any(media.matches(root, p, e['glob']) for e in cfg.get('spoken', [])):
                doc = extract.load(p, cfg.get('ignore_selectors', []))
                findings += media.check_spoken(root, p, cfg, doc)
    findings += check_pairs(root, paths, cfg)
    if root and cfg.get('label_sets'):
        hit = project or any(media.matches(root, p, e['file']) for p in paths for e in cfg['label_sets'])
        findings += media.check_labels(root, None, cfg) if hit else []
    if project:
        findings += media.check_colour_pairs(cfg, config.NAME)
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
    paths = args.files or sorted({str(p) for f in cfg['files'] for p in Path(root).glob(f['glob'])} |
                                 media.media_files(root, cfg))
    if not paths:
        print('No files to check. List them in .patient-info.json ("files") or pass them on the command line.')
        return 0
    scores = []
    findings = run(paths, root, cfg, args.lang, scores, project=not args.files)
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
    if not lang and str(Path(path).resolve()) not in {str(Path(p).resolve()) for p in media.media_files(root, cfg)}:
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


def cmd_contrast(args):
    lines = media.contrast_report(args.files)
    print('\n'.join(lines) or 'No CSS rule sets both a text colour and a background colour.')
    return 1 if any(l.endswith('FAIL') for l in lines) else 0


def cmd_cvd(args):
    for f in args.files:
        print(media.simulate(f, args.out))
    return 0


def cmd_panel(args):
    res = scoring.panel(scoring.load([args.file])[0], args.pass_share)
    print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else scoring.panel_report(res))
    return 0 if res['pass'] else 1


def cmd_agree(args):
    res = scoring.agree(scoring.load(args.files))
    print(json.dumps(res, ensure_ascii=False, indent=1) if args.json else scoring.agree_report(res))
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
    c = sub.add_parser('contrast', help='WCAG contrast of CSS rules that set text and background colour')
    c.add_argument('files', nargs='+')
    c = sub.add_parser('cvd', help='colour-blind previews of images (needs numpy and Pillow)')
    c.add_argument('files', nargs='+')
    c.add_argument('--out', help='folder for the previews (default: next to each image)')
    c = sub.add_parser('panel', help='tally a simulated reader panel (skill ai-reader-panel)')
    c.add_argument('file')
    c.add_argument('--pass-share', type=float, default=0.8, help='share of readers who must find and understand '
                   'each message (default 0.8 = MHRA 16 of 20)')
    c.add_argument('--json', action='store_true')
    c = sub.add_parser('agree', help='agreement between repeated AI scorings (skill scoring-reliability)')
    c.add_argument('files', nargs='+')
    c.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    return {'check': cmd_check, 'hook': cmd_hook, 'contrast': cmd_contrast, 'cvd': cmd_cvd, 'panel': cmd_panel,
            'agree': cmd_agree}[args.cmd](args)
