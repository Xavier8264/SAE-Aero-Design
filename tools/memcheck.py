#!/usr/bin/env python3
"""memcheck: read-only lint for the project memory files. Changes nothing.

Usage (run from anywhere):
  python tools/memcheck.py

Checks:
  PROJECT_MEMORY.md  ASCII only; append-only (the committed HEAD copy must be a prefix of the working
                     copy); entry headers '## [YYYY-MM-DD HH:MM ...' in time order (warning only).
  STATE.md           ASCII; <= 500 words; required sections; 'Reflects log through: [ts]' is not
                     older than the newest log entry (stale-cache check); every cited [ts] exists.
  DECISIONS.md       ASCII; unique row IDs; status in LOCKED/CURRENT/OPEN/SUPERSEDED; conf in
                     high/medium/low; every row cites at least one [ts] and every cited [ts] exists.
  Both derived files: backticked paths exist.

Prints one line per problem ([X] fail, [!] warning) and a summary. Exit code 1 if anything failed.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "PROJECT_MEMORY.md"
STATE = ROOT / "STATE.md"
DECISIONS = ROOT / "DECISIONS.md"

STATE_MAX_WORDS = 500
STATE_SECTIONS = ["Reflects log through:", "## Phase", "## Hardware", "## Key numbers",
                  "## BIG FLAG", "## Decisions in force", "## Open items", "## NEXT TASK"]
STATUSES = {"LOCKED", "CURRENT", "OPEN", "SUPERSEDED"}
CONFS = {"high", "medium", "low"}

HEADER_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", re.M)
CITE_RE = re.compile(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]")
TICK_RE = re.compile(r"`([^`\s]+)`")
PATHLIKE_RE = re.compile(r"(/|\.(py|md|txt|csv|json|xlsx)$)")

fails = []
warns = []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def read(path):
    """Return file text with LF line endings, or None if missing."""
    if not path.exists():
        fail(f"{path.name}: missing")
        return None
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return data.decode("latin-1")


def check_ascii(name, text):
    for n, line in enumerate(text.split("\n"), 1):
        bad = [c for c in line if ord(c) > 127]
        if bad:
            fail(f"{name}:{n}: non-ASCII byte 0x{ord(bad[0]):02X}")
            return


def check_paths(name, text):
    for n, line in enumerate(text.split("\n"), 1):
        for tok in TICK_RE.findall(line):
            if not PATHLIKE_RE.search(tok):
                continue
            rel = re.sub(r":\d+(-\d+)?$", "", tok)
            if not (ROOT / rel).exists():
                fail(f"{name}:{n}: path not found: {tok}")


def check_cites(name, text, headers):
    for n, line in enumerate(text.split("\n"), 1):
        for ts in CITE_RE.findall(line):
            if ts not in headers:
                fail(f"{name}:{n}: cites [{ts}] but no log entry has that timestamp")


def check_log():
    text = read(LOG)
    if text is None:
        return set(), None
    check_ascii(LOG.name, text)
    stamps = HEADER_RE.findall(text)
    if not stamps:
        fail(f"{LOG.name}: no entry headers found")
        return set(), None
    for prev, cur in zip(stamps, stamps[1:]):
        if cur < prev:
            warn(f"{LOG.name}: entry [{cur}] comes after [{prev}] (out of time order)")
    try:
        head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:PROJECT_MEMORY.md"],
                              capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        warn(f"{LOG.name}: append-only check skipped (no git or no committed copy)")
    else:
        head = head.replace(b"\r\n", b"\n").decode("latin-1")
        if not text.startswith(head):
            n = next((i for i, (a, b) in enumerate(zip(text, head)) if a != b), min(len(text), len(head)))
            line = text.count("\n", 0, n) + 1
            fail(f"{LOG.name}:{line}: committed text was changed or removed (file is append-only)")
    return set(stamps), max(stamps)


def check_state(headers, newest):
    text = read(STATE)
    if text is None:
        return
    check_ascii(STATE.name, text)
    words = len(text.split())
    if words > STATE_MAX_WORDS:
        fail(f"{STATE.name}: {words} words (max {STATE_MAX_WORDS})")
    for sec in STATE_SECTIONS:
        if sec not in text:
            fail(f"{STATE.name}: missing section '{sec}'")
    m = re.search(r"Reflects log through: \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]", text)
    if m and newest and m.group(1) < newest:
        fail(f"{STATE.name}: stale; reflects [{m.group(1)}] but the newest log entry is [{newest}]")
    check_cites(STATE.name, text, headers)
    check_paths(STATE.name, text)
    return words


def check_decisions(headers):
    text = read(DECISIONS)
    if text is None:
        return 0
    check_ascii(DECISIONS.name, text)
    ids = {}
    for n, line in enumerate(text.split("\n"), 1):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not re.fullmatch(r"[A-Z]\d+", cells[0]):
            continue
        rid = cells[0]
        if rid in ids:
            fail(f"{DECISIONS.name}:{n}: duplicate ID {rid} (first on line {ids[rid]})")
        ids.setdefault(rid, n)
        if len(cells) != 6:
            fail(f"{DECISIONS.name}:{n}: {rid} has {len(cells)} columns, expected 6")
            continue
        if cells[2] not in STATUSES:
            fail(f"{DECISIONS.name}:{n}: {rid} status '{cells[2]}' not in {sorted(STATUSES)}")
        if cells[3] not in CONFS:
            fail(f"{DECISIONS.name}:{n}: {rid} conf '{cells[3]}' not in {sorted(CONFS)}")
        if not CITE_RE.search(cells[4]):
            fail(f"{DECISIONS.name}:{n}: {rid} source cites no log entry [YYYY-MM-DD HH:MM]")
    check_cites(DECISIONS.name, text, headers)
    check_paths(DECISIONS.name, text)
    return len(ids)


def main():
    headers, newest = check_log()
    words = check_state(headers, newest)
    rows = check_decisions(headers)
    for msg in fails:
        print(f"[X] {msg}")
    for msg in warns:
        print(f"[!] {msg}")
    print(f"memcheck: log {len(headers)} timestamps, newest [{newest}]; STATE.md {words} words; "
          f"DECISIONS.md {rows} rows")
    print(f"memcheck: {'[OK]' if not fails else '[X]'} {len(fails)} fail, {len(warns)} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
