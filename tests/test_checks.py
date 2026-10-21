"""Run: python3 -m unittest discover tests"""
import unittest
from pathlib import Path

from pitk import checks, cli, config, media, readability, scoring

FIX = Path(__file__).parent / 'fixtures'


def rules(findings):
    return {f.rule for f in findings}


class TestChecks(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load(None)

    def test_english(self):
        r = rules(cli.check_file(FIX / 'leaflet-en.html', 'en', self.cfg))
        for rule in ['jargon', 'address-you', 'percent', 'verbal-risk', 'mixed-denominators', 'img-alt']:
            self.assertIn(rule, r)

    def test_neutral_mode_flags_you(self):
        cfg = dict(self.cfg, address_reader='neutral')
        doc = cli.extract.from_markdown('x.md', 'You may feel numb.')
        ck = checks.Checker(cfg)
        ck.english(doc)
        self.assertIn('address-neutral', rules(ck.out))

    def test_japanese(self):
        r = rules(cli.check_file(FIX / 'leaflet-ja.html', 'ja', self.cfg))
        for rule in ['ja-kanji', 'jargon', 'ja-keigo']:
            self.assertIn(rule, r)

    def test_kanji_lists(self):
        self.assertEqual(len(checks._kanji('kyouiku')), 1026)
        self.assertEqual(len(checks._kanji('jouyou')), 2136)

    def test_explained_term_is_not_jargon(self):
        doc = cli.extract.from_markdown('x.md', 'The jaw nerve (its medical name is the inferior alveolar nerve) runs here.')
        ck = checks.Checker(self.cfg)
        ck.common(doc, 'en')
        self.assertNotIn('jargon', rules(ck.out))

    def test_pair(self):
        a = cli.extract.load(FIX / 'leaflet-en.html')
        b = cli.extract.load(FIX / 'leaflet-ja.html')
        self.assertIn('pair-numbers', rules(checks.compare_pair(a, b, self.cfg)))


class TestReadability(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load(None)

    def check_en(self, text, **kw):
        ck = checks.Checker(dict(self.cfg, **kw))
        ck.english(cli.extract.from_markdown('x.md', text))
        return ck

    def test_easy_english_passes(self):
        ck = self.check_en('Your tooth sits near a nerve. The nerve lets you feel your lip. '
                           'Taking the tooth out can hurt the nerve. Your lip may feel numb for a while.')
        self.assertFalse({'en-smog', 'en-fre', 'en-fkgl'} & rules(ck.out))
        sc = ck.scores[0][2]
        self.assertEqual(set(sc) >= {'fkgl', 'smog', 'fre', 'fog', 'cli', 'ari'}, True)

    def test_hard_english_fails_smog_and_fre(self):
        ck = self.check_en('Postoperative neurosensory disturbance following mandibular third molar extraction is '
                           'predominantly attributable to inferior alveolar nerve compression. Radiographic '
                           'investigation facilitates individualised preoperative risk stratification. '
                           'Permanent paraesthesia occasionally necessitates microsurgical intervention.',
                           jargon_allow=['paraesthesia', 'extraction'])
        self.assertTrue({'en-smog', 'en-fre'} <= rules(ck.out))

    def test_smog_needs_three_sentences(self):
        ck = self.check_en('Postoperative neurosensory disturbance is predominantly attributable to compression. '
                           'Radiographic investigation facilitates individualised stratification.')
        self.assertIsNone(ck.scores[0][2]['smog'])
        self.assertNotIn('en-smog', rules(ck.out))

    def test_jreadability(self):
        sc = readability.ja_score('親知らずを抜くと神経が傷つくことがあります。下くちびるがしびれることがあります。')
        if sc is None:
            self.skipTest('fugashi + unidic-lite not installed')
        # Same text scored by the reference implementation (jreadability 1.1.5): 3.731.
        self.assertAlmostEqual(sc['jread'], 3.73, places=2)
        self.assertEqual(sc['sentences'], 2)
        self.assertEqual(readability.ja_level(5.6), '初級前半 lower elementary')
        self.assertEqual(readability.ja_level(3.0), '中級後半 upper intermediate')
        ck = checks.Checker(dict(self.cfg, ja_min_jread=5.0))
        ck.japanese(cli.extract.from_markdown('x.md', '親知らずを抜くと神経が傷つくことがあります。'))
        self.assertIn('ja-jread', rules(ck.out))

    def test_score_table(self):
        scores = []
        cli.check_file(FIX / 'leaflet-en.html', 'en', self.cfg, scores)
        self.assertIn('Flesch Reading Ease', cli.score_table(scores, None))


class TestNewChecks(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load(None)

    def test_claims(self):
        cfg = dict(self.cfg, claims=[{'value': '7 in 100', 'also': ['100人中約7人'], 'cite': ['rico']}])
        ck = checks.Checker(cfg)
        ck._claims(cli.extract.from_markdown('x.md', 'About 7 in 100 get it.[[rico]] About 9 in 100 do.[[rico]]\n\n'
                                                    'About 7 in 100 again.[[other]]'))
        msgs = [(f.rule, f.excerpt) for f in ck.out]
        self.assertTrue(any(r == 'claim-unknown' and '9 in 100' in e for r, e in msgs))
        self.assertTrue(any(r == 'claim-uncited' and 'again' in e for r, e in msgs))
        self.assertEqual(len(msgs), 2)
        self.assertEqual([v for v, _, _ in checks.risk_numbers('100人中約7人が')], ['7 in 100'])
        self.assertEqual([v for v, _, _ in checks.risk_numbers('About 1 to 3 in 1,000 people')], ['1-3 in 1000'])

    def test_alt_quality(self):
        doc = cli.extract.from_html('x.html', '<p>Hi there.</p><img src="a.png" alt="image"><img src="b.png" alt="b.png">'
                                    '<img src="c.png" alt="Picture of a tooth"><img src="d.png" alt="A tooth with long roots.">')
        ck = checks.Checker(self.cfg)
        ck.common(doc, 'en')
        self.assertEqual(sum(f.rule == 'img-alt-quality' for f in ck.out), 3)

    def test_contrast(self):
        self.assertAlmostEqual(media.contrast((0, 0, 0), (255, 255, 255)), 21.0, places=1)
        cfg = dict(self.cfg, colour_pairs=[['#E46C0A', '#FFFFFF', 'orange'], ['#E46C0A', '#FFFFFF', 'orange', 'large']])
        self.assertEqual(len(media.check_colour_pairs(cfg, 'x')), 1)
        rows = media.css_pairs(':root{--fg:#777}.a{color:var(--fg);background:#fff}.b{color:#000}')
        self.assertEqual(rows, [('.a', '#777', '#fff')])

    def test_subtitles_and_spoken(self):
        import tempfile, os
        d = tempfile.mkdtemp()
        vtt = os.path.join(d, 'v.vtt')
        Path(vtt).write_text('WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nThis line is far too long for one subtitle line, '
                             'really it is.\n', encoding='utf-8')
        cfg = dict(self.cfg, subtitles=[{'glob': '*.vtt', 'lang': 'en'}])
        rules_found = rules(media.check_subtitles(d, vtt, cfg))
        self.assertTrue({'sub-line-length', 'sub-reading-speed'} <= rules_found)
        self.assertAlmostEqual(media.spoken_seconds(' '.join(['word'] * 150), 'en', self.cfg), 60)

    def test_labels(self):
        import tempfile, os, json
        d = tempfile.mkdtemp()
        Path(d, 'a.html').write_text('<span class="label">Jaw nerve<small>inferior alveolar nerve</small></span>'
                                     '<span class="label">Roots</span>', encoding='utf-8')
        Path(d, 'b.json').write_text(json.dumps({'labels': {'n': ['Jaw nerve', 'x'], 't': ['Tooth', '']}}), encoding='utf-8')
        cfg = dict(self.cfg, label_sets=[{'file': 'a.html', 'selector': '.label'}, {'file': 'b.json', 'json': 'labels'}])
        out = media.check_labels(d, None, cfg)
        self.assertEqual(len(out), 1)
        self.assertIn('roots', out[0].message)

    def test_cvd(self):
        try:
            from PIL import Image
            import numpy  # noqa: F401
        except ImportError:
            self.skipTest('Pillow/numpy not installed')
        import tempfile, os
        d = tempfile.mkdtemp()
        p = os.path.join(d, 'red.png')
        Image.new('RGB', (20, 10), (200, 30, 30)).save(p)
        out = media.simulate(p)
        self.assertTrue(out.exists())

    def test_panel_and_agree(self):
        readers = [{'persona': f'r{i}', 'answers': {'q1': {'found': True, 'understood': i < 17},
                                                     'q2': {'found': i < 10, 'understood': True}}} for i in range(20)]
        res = scoring.panel({'questions': [{'id': 'q1'}, {'id': 'q2'}], 'readers': readers})
        self.assertEqual([q['pass'] for q in res['questions']], [True, False])
        runs = [{'instrument': 'PEMAT-P', 'sections': {'u': {'1': 'agree', '2': 'disagree', '3': 'na'}}},
                {'instrument': 'PEMAT-P', 'sections': {'u': {'1': 'agree', '2': 'agree', '3': 'na'}}},
                {'instrument': 'PEMAT-P', 'sections': {'u': {'1': 'agree', '2': 'disagree', '3': 'na'}}}]
        s = scoring.agree(runs)['sections']['u']
        self.assertEqual(s['scores'], [50.0, 100.0, 50.0])
        self.assertAlmostEqual(s['unanimous_share'], 0.67)
        self.assertIn('2', s['disputed'])


if __name__ == '__main__':
    unittest.main()
