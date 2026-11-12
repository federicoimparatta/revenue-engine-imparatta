#!/usr/bin/env python3
"""Fetch a structured board posting; print OPEN/CLOSED/UNKNOWN and first-posted age.

--url URL [--today YYYY-MM-DD]. Only OPEN with integer age_days>=30 qualifies.
No dates inferred from search snippets, updatedAt, page creation, or unrelated jobs.
"""
import argparse
from datetime import date, datetime
from html.parser import HTMLParser
import json
import re
import subprocess
import sys
from urllib.parse import urlsplit
from high_gate import JOB_BOARDS

CLOSED_HITS = ('no longer accepting applications', 'this job is closed',
               'this position has been filled', 'job is no longer available',
               'this job posting is no longer', 'posting has expired',
               'this role has been filled', 'applications are closed',
               'this job has been filled', 'job not found')


class JobHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json = False
        self.skip = False
        self.scripts, self.visible = [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'script', 'style'}:
            self.skip = True
            self.in_json = tag == 'script' and attrs.get('type') == 'application/ld+json'

    def handle_endtag(self, tag):
        if tag in {'script', 'style'}:
            self.skip = self.in_json = False

    def handle_data(self, data):
        if self.in_json:
            self.scripts.append(data)
        elif not self.skip:
            self.visible.append(data)


def jobs(value):
    if isinstance(value, list):
        for item in value:
            yield from jobs(item)
    elif isinstance(value, dict):
        types = value.get('@type', [])
        if types == 'JobPosting' or isinstance(types, list) and 'JobPosting' in types:
            yield value
        yield from jobs(value.get('@graph', []))


def parse_date(raw):
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace('Z', '+00:00')).date()
    except ValueError:
        return None


def inspect(body, status, url, today):
    if status in {404, 410, 451}:
        return f'CLOSED | reason=http-{status}'
    if status != 200:
        return f'UNKNOWN | reason=http-{status}'
    parser = JobHTML()
    parser.feed(body)
    text = ' '.join(parser.visible).lower()
    if any(hit in text for hit in CLOSED_HITS):
        return 'CLOSED | reason=closed-copy'
    records = []
    for script in parser.scripts:
        try:
            records.extend(jobs(json.loads(script)))
        except ValueError:
            continue
    # A single job API response is also structured evidence. Never accept a jobs list.
    try:
        data = json.loads(body)
        if isinstance(data, dict) and data.get('title') and data.get('id') and data.get('content'):
            records.append(data)
    except ValueError:
        pass
    if len(records) != 1:
        return 'UNKNOWN | reason=no-single-structured-job'
    job = records[0]
    if not (job.get('title') and (job.get('description') or job.get('content'))):
        return 'UNKNOWN | reason=incomplete-job'
    expiry = parse_date(job.get('validThrough'))
    if expiry and expiry < today:
        return 'CLOSED | reason=expired-validThrough'
    posted = next((parsed for key in ('datePosted', 'first_published', 'firstPublishedAt')
                   if (parsed := parse_date(job.get(key)))), None)
    if posted and posted > today:
        return 'UNKNOWN | reason=future-posted-date'
    age = (today - posted).days if posted else 'unknown'
    return f'OPEN | age_days={age} | posted={posted or "unknown"} | date_kind=first_posted'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url', required=True)
    ap.add_argument('--today', type=date.fromisoformat, default=date.today())
    a = ap.parse_args()
    try:
        parsed = urlsplit(a.url)
        if parsed.scheme not in {'http', 'https'} or parsed.hostname not in JOB_BOARDS:
            raise ValueError('url-not-allowed-board')
        proc = subprocess.run(['curl', '-sS', '-L', '--proto', '=http,https',
                               '--proto-redir', '=http,https', '--max-time', '25',
                               '-A', 'imparatta-lead-validator/1.0',
                               '-w', '\nHTTPSTATUS:%{http_code}', a.url],
                              capture_output=True, text=True, timeout=30)
        body, sep, status = proc.stdout.rpartition('\nHTTPSTATUS:')
        if proc.returncode or not sep:
            raise ValueError('fetch-failed')
        result = inspect(body, int(status), a.url, a.today)
        print(f'{result} | {a.url}')
        return 2 if result.startswith('UNKNOWN') else 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'UNKNOWN | reason={exc} | {a.url}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
