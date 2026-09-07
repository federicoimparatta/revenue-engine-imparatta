#!/usr/bin/env python3
"""Hunter.io email finder + verifier for the revenue-engine skill.

Uses curl for HTTPS (avoids the macOS python-ssl/certifi gap). Reads the API key
from $HUNTER_API_KEY or ~/.revenue-engine-imparatta/.secrets/hunter.env (gitignored).

Usage:
  python3 hunter_lookup.py account
  python3 hunter_lookup.py find   --domain acme.com --first Jane --last Doe
  python3 hunter_lookup.py verify --email jane@acme.com
  python3 hunter_lookup.py enrich --domain acme.com --first Jane --last Doe
      -> finds the address, then verifies it; prints one compact line.

`enrich` output line:
  <email or NOT_FOUND> | finder_score=NN | verify=<result>/<status> | deliverable=<yes|risky|no|unknown>
"""
import argparse, json, os, subprocess, sys, urllib.parse

API = "https://api.hunter.io/v2"


def load_key():
    k = os.environ.get("HUNTER_API_KEY")
    if k:
        return k.strip()
    env = os.path.expanduser("~/.revenue-engine-imparatta/.secrets/hunter.env")
    if os.path.exists(env):
        for line in open(env):
            if line.startswith("HUNTER_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("No HUNTER_API_KEY in env or ~/.revenue-engine-imparatta/.secrets/hunter.env")


def call(endpoint, params):
    params["api_key"] = load_key()
    url = f"{API}/{endpoint}?" + urllib.parse.urlencode(params)
    out = subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"errors": [{"details": out[:200]}]}


def deliverable(result, status):
    # Hunter result: deliverable | risky | undeliverable | unknown
    if result == "deliverable":
        return "yes"
    if result == "undeliverable":
        return "no"
    if status == "accept_all":
        return "risky"  # catch-all domain: cannot be confirmed
    if result == "risky":
        return "risky"
    return "unknown"


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("account")
    for name in ("find", "enrich"):
        p = sub.add_parser(name)
        p.add_argument("--domain", required=True)
        p.add_argument("--first", required=True)
        p.add_argument("--last", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--email", required=True)
    a = ap.parse_args()

    if a.cmd == "account":
        print(json.dumps(call("account", {}).get("data", {}), indent=2))
        return

    if a.cmd == "verify":
        d = call("email-verifier", {"email": a.email}).get("data", {})
        print(f"{a.email} | verify={d.get('result')}/{d.get('status')} | "
              f"deliverable={deliverable(d.get('result'), d.get('status'))} | score={d.get('score')}")
        return

    # find / enrich
    fd = call("email-finder", {"domain": a.domain, "first_name": a.first,
                               "last_name": a.last}).get("data", {})
    email = fd.get("email")
    score = fd.get("score")
    if not email:
        print(f"NOT_FOUND ({a.first} {a.last} @ {a.domain})")
        return
    if a.cmd == "find":
        print(f"{email} | finder_score={score}")
        return
    vd = call("email-verifier", {"email": email}).get("data", {})
    print(f"{email} | finder_score={score} | "
          f"verify={vd.get('result')}/{vd.get('status')} | "
          f"deliverable={deliverable(vd.get('result'), vd.get('status'))}")


if __name__ == "__main__":
    main()
