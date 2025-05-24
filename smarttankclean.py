#!/usr/bin/env python3
"""
clean.py – 1-3 Smart-Tank head-clean passes + optional verification sheet.

CLI
---
python3 clean.py --printer 192.168.178.30               # 1 cycle, no sheet
python3 clean.py --printer 192.168.178.30 --verify      # 1 + sheet
python3 clean.py --printer 192.168.178.30 --cycles 2    # 2, no sheets
python3 clean.py --printer 192.168.178.30 --cycles 3 --verify # 3 + sheets

Environment fallbacks
---------------------
PRINTER_IP   cycles=1   VERIFY=false   can all be set in env instead of args.
"""

from __future__ import annotations
import argparse, os, sys, time, xml.etree.ElementTree as ET
from urllib.parse import urljoin

import requests

# ─── constants ────────────────────────────────────────────────────────────
XML_TMPL = (
    '<ipdyn:InternalPrintDyn '
    'xmlns:ipdyn="http://www.hp.com/schemas/imaging/con/ledm/internalprintdyn/2008/03/21" '
    'xmlns:copy="http://www.hp.com/schemas/imaging/con/copy/2008/07/07" '
    'xmlns:dd="http://www.hp.com/schemas/imaging/con/dictionaries/1.0/" '
    'xmlns:dd3="http://www.hp.com/schemas/imaging/con/dictionaries/2009/04/06" '
    'xmlns:fw="http://www.hp.com/schemas/imaging/con/firewall/2011/01/05">'
        '<ipdyn:JobType>{job}</ipdyn:JobType>'
    '</ipdyn:InternalPrintDyn>'
)
NS = {"j": "http://www.hp.com/schemas/imaging/con/ledm/jobs/2009/04/30"}
JOB_FOR_LEVEL = {1: "cleaningPage", 2: "cleaningPageLevel2", 3: "cleaningPageLevel3"}
VERIFY_JOB = "cleaningVerificationPage"

# ─── job helpers ───────────────────────────────────────────────────────────
def submit_job(sess: requests.Session, printer: str, job_type: str) -> str:
    url = f"http://{printer}/DevMgmt/InternalPrintDyn.xml"
    r = sess.post(url, headers={"Content-Type": "text/xml"},
                  data=XML_TMPL.format(job=job_type), timeout=10)
    r.raise_for_status()
    return urljoin(f"http://{printer}/", r.headers["Location"])

def job_state(xml: str) -> str | None:
    try:
        root = ET.fromstring(xml)
        return root.findtext("j:JobState", namespaces=NS)
    except ET.ParseError:
        return None

def poll(sess: requests.Session, url: str) -> None:
    last = None
    while True:
        r = sess.get(url, headers={"Accept": "application/xml"}, timeout=6)
        state = job_state(r.text)
        if state and state != last:
            print("   ↳", state, flush=True)
            last = state
        if state in {"Completed", "Aborted", "Canceled"}:
            return
        time.sleep(5)

def run_cycle(sess: requests.Session, printer: str,
              level: int, add_sheet: bool) -> None:
    job = JOB_FOR_LEVEL[level]
    print(f"\n▶  Cleaning cycle {level}: {job}", flush=True)
    poll(sess, submit_job(sess, printer, job))
    if add_sheet:
        print("   Printing verification page …", flush=True)
        poll(sess, submit_job(sess, printer, VERIFY_JOB))

# ─── main ─────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--printer", help="printer IP/hostname "
                                     "(or set PRINTER_IP env)")
    p.add_argument("--cycles", type=int, choices=[1, 2, 3],
                   default=int(os.getenv("CYCLES", 1)))
    p.add_argument("--verify", action="store_true",
                   default=os.getenv("VERIFY", "false").lower() == "true",
                   help="print a sheet after EVERY cycle")
    args = p.parse_args()

    printer = args.printer or os.getenv("PRINTER_IP")
    if not printer:
        sys.exit("Set --printer or PRINTER_IP env var")

    if len(sys.argv) == 1 and "CYCLES" not in os.environ:
        print("ℹ️  Default: 1 cleaning cycle, no verification sheet.\n")

    with requests.Session() as sess:
        for lvl in range(1, args.cycles + 1):
            run_cycle(sess, printer, lvl, args.verify)

    print("\n🎉  All requested cycles finished.", flush=True)

if __name__ == "__main__":
    main()
