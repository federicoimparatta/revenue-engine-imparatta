#!/usr/bin/env python3
"""Fail-closed High gate. --record lead.json (or stdin), --today YYYY-MM-DD.

Required: vertical_match=in_vertical, geography_fit=in_geo|remote, stage=seed|
seed extension|pre-a|series a|series b, stage_ok=true, offer_fit=<services offer>,
source_url, source_date=YYYY-MM-DD, excluded=false, duplicate_domain=false,
dealbreaker=false, signal_type=stuck leadership hire|fresh raise.
Hires also need job_status=OPEN, job_age_days>=30 matching source_date,
job_date_kind=first_posted, job_title, and an allowed board source URL.
Raises need raise_stage=seed|seed extension|pre-a|series a and
raise_mentions_product_or_ai=true; source must be 0-60 days old.
HIGH / NOT_HIGH exit 0; bad input exits 2. Save the record and verdict as evidence.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

STAGES = {'seed', 'seed extension', 'pre-a', 'series a', 'series b'}
RAISE_STAGES = STAGES - {'series b'}
JOB_BOARDS = {'boards.greenhouse.io', 'job-boards.greenhouse.io', 'boards-api.greenhouse.io',
              'jobs.ashbyhq.com', 'api.ashbyhq.com', 'jobs.lever.co', 'api.lever.co',
              'wellfound.com', 'fractionals.work'}
LEADERSHIP = re.compile(r'\b(cpo|chief product officer|head of (?:product|delivery|ai|data|artificial intelligence))\b', re.I)


def evaluate(rec, today):
    reasons = []
    for field, reason in [('excluded', 'excluded-or-unchecked'),
                          ('duplicate_domain', 'duplicate-domain-or-unchecked'),
                          ('dealbreaker', 'dealbreaker-or-unchecked')]:
        if rec.get(field) is not False:
            reasons.append(reason)
    if rec.get('vertical_match') != 'in_vertical':
        reasons.append('vertical-not-direct')
    if rec.get('geography_fit') not in {'in_geo', 'remote'}:
        reasons.append('geo-not-in-scope')
    if rec.get('stage_ok') is not True or rec.get('stage') not in STAGES:
        reasons.append('stage-not-seed-to-b')
    offer = rec.get('offer_fit')
    if not isinstance(offer, str) or not offer.strip() or offer.lower() in {'no_fit', 'general', 'unknown'}:
        reasons.append('no-offer-fit')
    signal = rec.get('signal_type')
    if signal not in {'stuck leadership hire', 'fresh raise'}:
        reasons.append('signal-cannot-be-high')
    url = rec.get('source_url')
    parsed = urlsplit(url) if isinstance(url, str) else urlsplit('')
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        reasons.append('missing-source-url')
    try:
        age = (today - date.fromisoformat(rec.get('source_date', ''))).days
    except (ValueError, TypeError):
        age = None
        reasons.append('source-date-unknown')
    if age is not None and age < 0:
        reasons.append('source-date-in-future')
    if signal == 'stuck leadership hire':
        if rec.get('job_status') != 'OPEN':
            reasons.append('job-not-open')
        if parsed.hostname not in JOB_BOARDS:
            reasons.append('job-source-not-allowed')
        if not LEADERSHIP.search(str(rec.get('job_title', ''))):
            reasons.append('job-not-target-leadership')
        if rec.get('job_date_kind') != 'first_posted':
            reasons.append('job-first-posted-date-unverified')
        job_age = rec.get('job_age_days')
        if type(job_age) is not int or age is None or job_age != age:
            reasons.append('job-age-unverified')
        elif age < 30:
            reasons.append('job-younger-than-30-days')
    elif signal == 'fresh raise':
        if rec.get('raise_stage') not in RAISE_STAGES:
            reasons.append('raise-not-seed-or-a')
        if rec.get('raise_mentions_product_or_ai') is not True:
            reasons.append('raise-no-product-or-ai-buildout')
        if age is not None and age > 60:
            reasons.append('raise-older-than-60-days')
    return reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--record')
    ap.add_argument('--today', type=date.fromisoformat, default=date.today())
    a = ap.parse_args()
    try:
        rec = json.loads(Path(a.record).read_text() if a.record else sys.stdin.read())
        if not isinstance(rec, dict):
            raise ValueError('record must be a JSON object')
        reasons = evaluate(rec, a.today)
        print('NOT_HIGH | ' + '; '.join(reasons) if reasons else 'HIGH')
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(f'ERROR | {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
