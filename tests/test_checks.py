"""Run: python3 -m unittest discover tests"""
import unittest
from pathlib import Path

from pitk import checks, cli, config, readability

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


if __name__ == '__main__':
    unittest.main()
