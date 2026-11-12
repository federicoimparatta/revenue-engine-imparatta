#!/usr/bin/env python3
"""Normalize website/email domains using the bundled Mozilla Public Suffix List.

normalize VALUE; check-exclude --company NAME --domain HOST --email EMAIL
--exclude-file FILE; in-set --domain HOST --set-file FILE.
Exclusion/duplicate exits 1; invalid input exits 2. No network lookups.
"""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


def ascii_host(host):
    return host.lower().strip('.').encode('idna').decode('ascii')


def load_suffixes():
    rules = Path(__file__).with_name('public_suffix_list.dat').read_text()
    return {ascii_host(line.strip()) for line in rules.splitlines()
            if line.strip() and not line.startswith('//')}


SUFFIXES = load_suffixes()


def registrable(raw):
    if not isinstance(raw, str) or not raw.strip():
        return ''
    raw = raw.strip()
    if '://' not in raw and not raw.startswith('//'):
        raw = '//' + raw.rsplit('@', 1)[-1]
    try:
        parsed = urlsplit(raw)
        host = ascii_host(parsed.hostname or '')
        if parsed.scheme and parsed.scheme not in {'http', 'https'}:
            return ''
    except (ValueError, UnicodeError):
        return ''
    try:
        ipaddress.ip_address(host)
        return ''  # IPs are not company domains.
    except ValueError:
        pass
    if not host or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', p)
                       for p in host.split('.')):
        return ''
    labels = host.split('.')
    suffix_size = 1
    for i in range(len(labels)):
        tail = '.'.join(labels[i:])
        if '!' + tail in SUFFIXES:
            suffix_size = len(labels) - i - 1
            break
        if tail in SUFFIXES or (i + 1 < len(labels) and '*.' + '.'.join(labels[i + 1:]) in SUFFIXES):
            suffix_size = max(suffix_size, len(labels) - i)
    if len(labels) <= suffix_size:
        return ''
    return '.'.join(labels[-suffix_size - 1:])


def excluded(company, domain, email, rules):
    # Check BOTH domains: an unrelated website must never mask a client email.
    domains = {registrable(domain), registrable(email)} - {''}
    reasons = []
    for rule in rules:
        for raw in rule.get('domains', []):
            dom = registrable(raw)
            if dom and dom in domains and f'domain:{dom}' not in reasons:
                reasons.append(f'domain:{dom}')
        for name in rule.get('names', []):
            if re.search(r'(?<![a-z0-9])' + re.escape(name.lower()) + r'(?![a-z0-9])',
                         (company or '').lower()):
                reasons.append(f'name:{name}')
    return reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('normalize').add_argument('value')
    check = sub.add_parser('check-exclude')
    check.add_argument('--company', default='')
    check.add_argument('--domain', default='')
    check.add_argument('--email', default='')
    check.add_argument('--exclude-file', required=True)
    seen = sub.add_parser('in-set')
    seen.add_argument('--domain', required=True)
    seen.add_argument('--set-file', required=True)
    a = ap.parse_args()
    try:
        if a.cmd == 'normalize':
            dom = registrable(a.value)
            print(dom or 'UNKNOWN')
            return 0 if dom else 2
        if a.cmd == 'check-exclude':
            rules = json.loads(Path(a.exclude_file).read_text())
            if not isinstance(rules, list) or not rules:
                raise ValueError('exclusion file must contain a nonempty rules list')
            hits = excluded(a.company, a.domain, a.email, rules)
            print('EXCLUDE | ' + '; '.join(hits) if hits else 'OK')
            return 1 if hits else 0
        dom = registrable(a.domain)
        if not dom:
            raise ValueError('unknown domain; do not treat as NEW')
        domains = {registrable(x.strip()) for x in Path(a.set_file).read_text().splitlines()}
        print(f'DUPLICATE | {dom}' if dom in domains else f'NEW | {dom}')
        return 1 if dom in domains else 0
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(f'ERROR | {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
