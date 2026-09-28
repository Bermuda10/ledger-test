#!/usr/bin/env python3
"""Builds every ledger file from tools/source.json.

One source, two renderings. The .json files are what the website reads.
The .md files are what a person reads on GitHub. They never disagree
because both come from the same source in the same run. The commit bot
(commit-to-ledger) produces exactly this output for one entry at a time.

Usage: python3 tools/build.py
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = json.loads((ROOT / "tools" / "source.json").read_text())

TEST_BANNER = (
    "> **Test ledger.** Every organisation, entry, signature count and reading "
    "in this repository is invented to rehearse the process. Nothing here is on "
    "the record. The real ledger is `bermuda10/ledger`.\n\n"
)
BANNER = TEST_BANNER if SRC["test"] else ""


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def dump(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def entry_base(e):
    return f"entries/{e['number']:03d}-{e['slug']}"


def public_entry(e):
    """The JSON shape the site renders from. Drops builder-only keys."""
    return dict(e)


def render_goals(entry, parent):
    lines = []
    fl = entry["fairness_test"]
    pfl = parent["fairness_test"] if parent else None
    lines.append("### This version's test of fairness\n")
    if fl["action"] == "amend" and pfl:
        lines.append(f"**Amend.** *{fl['wording']}*\n")
        lines.append(f"Was: ~~{pfl['wording']}~~\n")
        lines.append(f"Why: {fl['why']}\n")
    else:
        lines.append(f"*{fl['wording']}*\n")
    for g in entry["goals"]:
        n = g["slot"]
        pg = next((x for x in parent["goals"] if x["slot"] == n), None) if parent else None
        lines.append(f"### {n}. {g['short_name']}, {g['title']}\n")
        if g["action"] == "keep" or pg is None:
            lines.append(g["wording"] + "\n")
        else:
            lines.append(f"**{g['action'].capitalize()}.** {g['wording']}\n")
            lines.append(f"Was: ~~{pg['wording']}~~")
            if pg["title"] != g["title"] or pg["short_name"] != g["short_name"]:
                lines.append(f"Was titled: ~~{pg['short_name']}, {pg['title']}~~")
            lines.append("")
            lines.append(f"Why: {g['why']}\n")
    return "\n".join(lines)


def render_entry(e, entries):
    parent = next((x for x in entries if x["number"] == e.get("built_from")), None)
    md = [BANNER + f"# {e['number']:03d} · {e['title']}\n"]
    md.append("| | |\n|---|---|")
    md.append(f"| Type | {e['type']} |")
    if e["type"] == "genesis":
        md.append(f"| Tabled by | {e['signer']['name']}, as a resident |")
    else:
        o = e["organisation"]
        md.append(f"| Tabled by | {o['name']} ({o['kind']}) |")
        md.append(f"| Authorised signer | {e['signer']['name']}, {e['signer']['role']} |")
    if parent:
        md.append(f"| Built from | {parent['number']:03d} |")
    if e.get("revision_of"):
        md.append(f"| Revision of | {e['revision_of']:03d} |")
    md.append(f"| Published | {e['published_at']} |")
    md.append(f"| Status | {e['status']} |")
    md.append(f"| Signable | {'no, never, by anyone' if e['type'] == 'genesis' else 'yes, from organisations and residents'} |")
    changed = sum(1 for g in e["goals"] if g["action"] != "keep") + (1 if e["fairness_test"]["action"] != "keep" else 0)
    if parent:
        md.append(f"| Changes | {'kept all ten' if changed == 0 else str(changed) + ' changed'} |")
    md.append(f"| Licence | {e['licence']} |")
    md.append("")
    if e.get("preamble"):
        md.append(e["preamble"] + "\n")
    md.append("## The Ten\n")
    md.append(render_goals(e, parent))
    if e.get("authors"):
        md.append("## Authors (credits, not signatures)\n")
        md.extend(f"- {a['name']}, {a['role']}" for a in e["authors"])
        md.append("")
    md.append("## Co-signed by\n")
    if e["type"] == "genesis":
        md.append("Genesis cannot be co-signed. Table your own copy.\n")
    elif e.get("co_signed_by"):
        md.extend(f"- {j['organisation']}, {j['signer_role']}, {j['date']}" for j in e["co_signed_by"])
        md.append("")
    else:
        md.append("No co-signs yet.\n")
    md.append("## The four gates, attested by the tabler, never judged\n")
    for k, v in e["gates_attested"].items():
        md.append(f"- {k}: {'attested' if v else 'not attested'}")
    md.append("")
    md.append("Resident signature counts live in `readings/`, taken at every month-end. "
              "No individual signer appears in this repository.\n")
    base = entry_base(e)
    write(base + ".md", "\n".join(md))
    dump(base + ".json", public_entry(e))
    return base


def render_reading(r):
    md = [BANNER + f"# Reading · {r['period']}\n"]
    md.append(f"Cutoff {r['cutoff_at']}. Run {r['ran_at']}.\n")
    md.append("A reading records every answer's backing at the cutoff. It declares nothing: "
              "no leading version, no threshold, no winner. The rule by which an answer comes to be "
              "measured against is written with the participants and published before it applies.\n")
    md.append("| Entry | Co-signs | Signatures | Walks | Named | Unnamed | Under review |")
    md.append("|---|---|---|---|---|---|---|")
    for t in r["tallies"]:
        md.append(f"| {t['entry']:03d} | {t['co_signs']} | {t['signatures']} | {t['walks']} | {t['named']} | "
                  f"{t['unnamed']} | {t['under_review']} |")
    md.append("")
    md.append("Spread by walk, per entry:\n")
    for t in r["tallies"]:
        md.append(f"- {t['entry']:03d}: " + ", ".join(f"{w} {c}" for w, c in t["by_walk"].items()))
    md.append("")
    if r.get("note"):
        md.append(r["note"] + "\n")
    write(f"readings/{r['period']}.md", "\n".join(md))
    dump(f"readings/{r['period']}.json", r)


def render_brake(b):
    name = f"brake/{b['date']}-{b['kind']}"
    md = [BANNER + f"# Brake · {b['date']} · {b['kind']}\n"]
    md.append("| | |\n|---|---|")
    md.append(f"| Kind | {b['kind']} |")
    if b.get("entry"):
        md.append(f"| Entry | {b['entry']:03d} |")
    md.append(f"| Starts | {b['starts_at']} |")
    md.append(f"| Ends | {b.get('ends_at') or 'on resolution'} |")
    md.append(f"| Recorded by | {b['recorded_by']} |")
    md.append("")
    md.append(f"**Reason.** {b['reason']}\n")
    md.append("The brake slows. It never steers. An administrator cannot edit an entry, "
              "change a count, delete anything, run a reading early or choose a version.\n")
    write(name + ".md", "\n".join(md))
    dump(name + ".json", b)
    return name + ".json"


def check(src):
    """The repository must never disagree with itself. A reading's co-sign
    count for an entry must equal the co-signs on that entry dated at or
    before the cutoff. Build refuses otherwise."""
    by_number = {e["number"]: e for e in src["entries"]}
    for r in src["readings"]:
        cutoff = r["cutoff_at"][:10]
        for t in r["tallies"]:
            e = by_number[t["entry"]]
            have = sum(1 for c in e.get("co_signed_by", []) if c["date"] <= cutoff)
            if have != t["co_signs"]:
                raise SystemExit(f"reading {r['period']}: entry {t['entry']:03d} has {have} "
                                 f"co-signs by the cutoff, tally says {t['co_signs']}")
    for e in src["entries"]:
        if e["type"] == "genesis" and e.get("co_signed_by"):
            raise SystemExit("Genesis cannot be co-signed")
        if len(e["goals"]) != 10 or sorted(g["slot"] for g in e["goals"]) != list(range(1, 11)):
            raise SystemExit(f"entry {e['number']:03d} does not have slots 1 to 10")


def main():
    check(SRC)
    for d in ("entries", "readings", "brake", "settings"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    entries = SRC["entries"]
    paths = {e["number"]: render_entry(e, entries) for e in entries}
    for r in SRC["readings"]:
        render_reading(r)
    brake_paths = [render_brake(b) for b in SRC["brake"]]
    for s in SRC["settings"]:
        dump(f"settings/{s['effective_from']}.json", s)
    dump("not-admitted.json", SRC["not_admitted"])

    latest = SRC["readings"][-1] if SRC["readings"] else None
    index = {
        "test": SRC["test"],
        "repository": SRC["repository"],
        "licence": "CC BY 4.0",
        "convergence_rule": None,
        "last_reading": latest["period"] if latest else None,
        "entries": [
            {
                "number": e["number"],
                "slug": e["slug"],
                "type": e["type"],
                "organisation": e["organisation"]["name"] if e.get("organisation") else None,
                "signer": e["signer"]["name"],
                "built_from": e.get("built_from"),
                "revision_of": e.get("revision_of"),
                "published_at": e["published_at"],
                "status": e["status"],
                "signable": e["type"] != "genesis",
                "co_signs": len(e.get("co_signed_by", [])),
                "changes": "kept all ten" if e.get("built_from") and all(g["action"] == "keep" for g in e["goals"]) and e["fairness_test"]["action"] == "keep" else None,
                "path": paths[e["number"]] + ".json",
            }
            for e in entries
        ],
        "readings": [f"readings/{r['period']}.json" for r in SRC["readings"]],
        "brake": brake_paths,
        "settings": [f"settings/{s['effective_from']}.json" for s in SRC["settings"]],
        "not_admitted": "not-admitted.json",
    }
    dump("index.json", index)
    print("built", len(entries), "entries,", len(SRC["readings"]), "readings,",
          len(SRC["brake"]), "brake records")


if __name__ == "__main__":
    main()
