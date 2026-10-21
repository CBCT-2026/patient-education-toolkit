"""Run: python3 -m unittest discover tests"""
import unittest
from pathlib import Path

from pitk import checks, cli, config

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


if __name__ == '__main__':
    unittest.main()
