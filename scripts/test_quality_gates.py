#!/usr/bin/env python3
"""Offline gate/contact/domain/posting regression tests. No API calls or drafts."""
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
import json
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

from domain_util import excluded, registrable
from high_gate import evaluate
from hunter_lookup import deliverable, finder_passes, main as hunter_main
from validate_job_posting import inspect

TODAY = date(2026, 11, 12)


def lead(**updates):
    result = dict(vertical_match='in_vertical', geography_fit='in_geo', stage='series a',
                  stage_ok=True, offer_fit='AI demo to production', signal_type='fresh raise',
                  source_url='https://example.com/raise', source_date='2026-10-13',
                  raise_stage='series a', raise_mentions_product_or_ai=True,
                  excluded=False, duplicate_domain=False, dealbreaker=False)
    result.update(updates)
    return result


def hire(**updates):
    result = lead(signal_type='stuck leadership hire', source_url='https://jobs.lever.co/acme/123',
                  job_status='OPEN', job_age_days=30, job_date_kind='first_posted',
                  job_title='Head of Product')
    result.update(updates)
    return result


def page(**updates):
    job = {'@type': 'JobPosting', 'title': 'Head of Product',
           'description': 'Lead product. Apply today.', 'datePosted': '2026-10-13'}
    job.update(updates)
    return '<script type="application/ld+json">' + json.dumps(job) + '</script><h1>Head of Product</h1>'


class HighGateTests(TestCase):
    def test_valid_hire_raise_and_remote(self):
        for record in [lead(), hire(), lead(geography_fit='remote'), hire(stage='series b')]:
            with self.subTest(record=record):
                self.assertEqual(evaluate(record, TODAY), [])

    def test_retired_and_unsupported_signals(self):
        for signal in ['shipping stall', 'leadership departure', 'other', None]:
            self.assertIn('signal-cannot-be-high', evaluate(lead(signal_type=signal), TODAY))

    def test_every_required_dimension_fails_closed(self):
        for key in ['vertical_match', 'geography_fit', 'stage', 'stage_ok', 'offer_fit',
                    'source_url', 'source_date', 'excluded', 'duplicate_domain', 'dealbreaker']:
            record = lead()
            record.pop(key)
            with self.subTest(key=key):
                self.assertTrue(evaluate(record, TODAY))
        for key in ['excluded', 'duplicate_domain', 'dealbreaker']:
            self.assertTrue(evaluate(lead(**{key: True}), TODAY))

    def test_raise_window(self):
        self.assertEqual(evaluate(lead(source_date='2026-09-13'), TODAY), [])  # 60 days
        for stamp in ['2026-09-12', '2026-11-13', '', None, 123]:
            with self.subTest(stamp=stamp):
                self.assertTrue(evaluate(lead(source_date=stamp), TODAY))
        self.assertTrue(evaluate(lead(raise_stage='series b'), TODAY))
        self.assertTrue(evaluate(lead(stage='series c'), TODAY))
        self.assertTrue(evaluate(lead(raise_mentions_product_or_ai=False), TODAY))

    def test_hire_age_source_liveness_and_title(self):
        for changes in [dict(job_status='CLOSED'), dict(job_status='UNKNOWN'),
                        dict(job_age_days=None), dict(job_age_days='30'),
                        dict(job_age_days=29, source_date='2026-10-14'),
                        dict(job_age_days=35), dict(source_date=None),
                        dict(job_date_kind='last_updated'), dict(job_title='Software Engineer'),
                        dict(source_url='https://example.com/jobs/123')]:
            with self.subTest(changes=changes):
                self.assertTrue(evaluate(hire(**changes), TODAY))
        self.assertEqual(evaluate(hire(job_age_days=407, source_date='2025-10-01'), TODAY), [])
        for title in ['CPO', 'Chief Product Officer', 'Head of Delivery', 'Head of AI', 'Head of Data']:
            self.assertEqual(evaluate(hire(job_title=title), TODAY), [])


class DomainTests(TestCase):
    def test_equivalent_hosts_and_email(self):
        for value in ['ACME.com', 'www.acme.com', 'jobs.acme.com', 'https://www.acme.com/careers',
                      'Jane@jobs.acme.com', '//jobs.acme.com:443/path', 'https://acme.com./']:
            self.assertEqual(registrable(value), 'acme.com')

    def test_suffixes_and_bad_input(self):
        for raw, expected in [('careers.acme.co.uk', 'acme.co.uk'), ('www.acme.com.uy', 'acme.com.uy'),
                              ('jobs.acme.github.io', 'acme.github.io'), ('www.city.kawasaki.jp', 'city.kawasaki.jp'),
                              ('https://[bad', ''), ('localhost', ''), ('127.0.0.1', ''),
                              ('co.uk', ''), ('', '')]:
            with self.subTest(raw=raw):
                self.assertEqual(registrable(raw), expected)

    def test_email_cannot_hide_behind_different_website(self):
        rules = [dict(names=['Nike'], domains=['nike.com'])]
        self.assertTrue(excluded('Acme', 'acme.com', 'jane@careers.nike.com', rules))
        self.assertTrue(excluded('NIKE Inc', '', '', rules))
        self.assertFalse(excluded('Niken', 'niken.com', '', rules))
        self.assertFalse(excluded('Neuron7', 'neuron7.ai', '', rules))


class ContactTests(TestCase):
    def test_finder_score_floor(self):
        for score in [80, 91, 100]:
            self.assertTrue(finder_passes(score))
        for score in [79, None, '91', True, float('nan'), 101]:
            self.assertFalse(finder_passes(score))
        self.assertEqual(deliverable('deliverable', 'accept_all'), 'risky')
        self.assertEqual(deliverable('deliverable', 'valid'), 'yes')
        self.assertEqual(deliverable('unknown', 'unknown'), 'unknown')

    def test_enrich_marks_below_floor_ineligible(self):
        for score, result, status, expected in [(79, 'deliverable', 'valid', 'no'),
                                               (None, 'deliverable', 'valid', 'no'),
                                               (80, 'deliverable', 'valid', 'yes'),
                                               (95, 'deliverable', 'accept_all', 'no')]:
            responses = [{'data': {'email': 'jane@acme.com', 'score': score}},
                         {'data': {'result': result, 'status': status}}]
            output = StringIO()
            with patch('hunter_lookup.call', side_effect=responses), redirect_stdout(output), \
                 patch('sys.argv', ['hunter_lookup.py', 'enrich', '--domain', 'acme.com',
                                    '--first', 'Jane', '--last', 'Doe']):
                hunter_main()
            self.assertIn('email_eligible=' + expected, output.getvalue())


class PostingTests(TestCase):
    def check(self, body, status=200):
        return inspect(body, status, 'https://jobs.lever.co/acme/123', TODAY)

    def test_live_age_verified(self):
        self.assertIn('OPEN | age_days=30 | posted=2026-10-13', self.check(page()))

    def test_individual_greenhouse_api_and_no_updated_date_fallback(self):
        body = json.dumps(dict(id=123, title='Head of Product', content='Apply now',
                               first_published='2026-10-13', updated_at='2026-11-10'))
        self.assertIn('OPEN | age_days=30', self.check(body))
        self.assertIn('age_days=unknown', self.check(json.dumps(dict(
            id=123, title='Head of Product', content='Apply now', updated_at='2026-09-01'))))

    def test_closed_and_expired(self):
        self.assertTrue(self.check('gone', 404).startswith('CLOSED'))
        self.assertTrue(self.check(page() + 'This job is closed').startswith('CLOSED'))
        self.assertTrue(self.check(page(validThrough='2026-11-11')).startswith('CLOSED'))

    def test_fetch_errors_are_not_open(self):
        for body, status in [('Forbidden', 403), ('rate limited', 429), ('oops', 500),
                             ('<h1>Job board</h1>', 200), ('', 200)]:
            self.assertTrue(self.check(body, status).startswith('UNKNOWN'))

    def test_no_age_guesses_or_unrelated_dates(self):
        self.assertIn('age_days=unknown', self.check(page(datePosted=None, updatedAt='2026-09-01')))
        self.assertTrue(self.check(page(datePosted='2026-11-13')).startswith('UNKNOWN'))
        self.assertTrue(self.check(page() + page()).startswith('UNKNOWN'))


if __name__ == '__main__':
    main(verbosity=2)
