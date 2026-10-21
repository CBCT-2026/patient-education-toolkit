"""Tally AI-scored reviews. The judging is done by Claude (skills ai-reader-panel and scoring-reliability); these
functions only add up the saved results, so the numbers are reproducible from the JSON files.

  pitk panel results.json              reader panel: share of readers who found and understood each key message
  pitk agree run1.json run2.json ...   repeated PEMAT / CDC scoring: mean score, spread, item agreement, Fleiss' kappa
"""
import json
import statistics
from collections import Counter
from pathlib import Path


# ---------- reader panel ----------
def panel(data, pass_share=0.8):
    """data = {"questions": [{"id", "message"}], "readers": [{"persona", "answers": {id: {"found": bool,
    "understood": bool}}}]}. MHRA benchmark: each message found and understood by 16 of 20 readers (80%)."""
    qs, readers = data['questions'], data['readers']
    rows, ok = [], True
    for q in qs:
        res = [r['answers'].get(q['id'], {}) for r in readers]
        found = sum(bool(a.get('found')) for a in res)
        both = sum(bool(a.get('found')) and bool(a.get('understood')) for a in res)
        passed = both >= pass_share * len(readers)
        ok &= passed
        missed = [r['persona'] for r, a in zip(readers, res) if not (a.get('found') and a.get('understood'))]
        rows.append({'id': q['id'], 'message': q.get('message', ''), 'found': found, 'found_and_understood': both,
                     'readers': len(readers), 'pass': passed, 'missed_by': missed})
    return {'pass': ok, 'pass_share': pass_share, 'questions': rows}


def panel_report(res):
    lines = [f'Reader panel (simulated): pass mark {res["pass_share"]:.0%} of readers find and understand each message.']
    for r in res['questions']:
        lines.append(f'  {"PASS" if r["pass"] else "FAIL"} {r["id"]}: {r["found_and_understood"]}/{r["readers"]} found and '
                     f'understood ({r["found"]} found). {r["message"]}')
        if r['missed_by']:
            lines.append(f'       missed by: {", ".join(r["missed_by"])}')
    lines.append('Overall: ' + ('PASS' if res['pass'] else 'FAIL') +
                 '. Simulated readers are a pre-test only, not a substitute for testing with real readers.')
    return '\n'.join(lines)


# ---------- repeated scoring ----------
POS = {'agree', 'yes', '1', 'true'}
NA = {'na', 'n/a', 'not applicable'}


def run_score(items):
    vals = [str(v).strip().lower() for v in items.values()]
    applicable = [v for v in vals if v not in NA]
    return 100 * sum(v in POS for v in applicable) / len(applicable) if applicable else None


def fleiss_kappa(table):
    """table: one Counter of category -> number of runs per item. All items rated by the same number of runs."""
    if not table or sum(table[0].values()) < 2:
        return None
    n = sum(table[0].values())
    cats = sorted({c for row in table for c in row})
    N = len(table)
    p = [sum(row[c] for row in table) / (N * n) for c in cats]
    P = [(sum(row[c] ** 2 for c in cats) - n) / (n * (n - 1)) for row in table]
    Pbar, Pe = sum(P) / N, sum(x * x for x in p)
    return 1.0 if Pe == 1 else (Pbar - Pe) / (1 - Pe)


def agree(runs):
    """runs = [{"instrument": "PEMAT-P", "sections": {"understandability": {item: answer}, ...}}, ...] or a flat
    {"items": {...}}. Returns per-section mean and spread of scores, share of items all runs agree on, and kappa."""
    def sections(r):
        return r.get('sections') or {'score': r['items']}
    names = list(sections(runs[0]))
    out = {'instrument': runs[0].get('instrument', ''), 'runs': len(runs), 'sections': {}}
    for name in names:
        per_run = [{str(k): str(v).strip().lower() for k, v in sections(r)[name].items()} for r in runs]
        items = sorted(set().union(*per_run), key=lambda x: (len(x), x))
        scores = [run_score(r) for r in per_run]
        table = [Counter(r.get(i, 'missing') for r in per_run) for i in items]
        unanimous = [i for i, row in zip(items, table) if len(row) == 1]
        disputed = {i: dict(row) for i, row in zip(items, table) if len(row) > 1}
        valid = [s for s in scores if s is not None]
        out['sections'][name] = {
            'scores': [None if s is None else round(s, 1) for s in scores],
            'mean': round(statistics.mean(valid), 1) if valid else None,
            'sd': round(statistics.stdev(valid), 1) if len(valid) > 1 else 0.0,
            'items': len(items), 'unanimous_share': round(len(unanimous) / len(items), 2) if items else None,
            'fleiss_kappa': None if fleiss_kappa(table) is None else round(fleiss_kappa(table), 2),
            'disputed': disputed,
        }
    return out


def agree_report(res):
    lines = [f'{res["instrument"]}: {res["runs"]} independent runs']
    for name, s in res['sections'].items():
        lines.append(f'  {name}: mean {s["mean"]} (SD {s["sd"]}; runs {s["scores"]}); all runs agree on '
                     f'{s["unanimous_share"]:.0%} of {s["items"]} items; Fleiss kappa {s["fleiss_kappa"]}')
        for item, votes in s['disputed'].items():
            lines.append(f'     item {item}: {votes}')
    return '\n'.join(lines)


def load(paths):
    return [json.loads(Path(p).read_text(encoding='utf-8')) for p in paths]
