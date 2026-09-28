#!/usr/bin/env python3
"""Builds every ledger file from tools/source.json.

One source, two renderings. The .json files are what the website reads.
The .md files are what a person reads on GitHub. They never disagree
because both come from the same source in the same run.

Usage: python3 tools/build.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = json.loads((ROOT / "tools" / "source.json").read_text())

TEST_BANNER = (
    "> **Test ledger.** Every organisation, entry, signature count and reading "
    "in this repository is invented to rehearse the process. Nothing here is on "
    "the record. The real ledger is `bermuda10/ledger`.\n\n"
)


def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")


def entry_path(e):
    n = f"{e['number']:03d}"
    name = "genesis" if e["kind"] == "genesis" else slug(e["organisation"]["short_name"])
    return f"entries/{n}-{name}"


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def dump(path, obj):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def goals_table(entry, parent):
    lines = []
    for g in entry["goals"]:
        n = g["number"]
        pg = next((x for x in parent["goals"] if x["number"] == n), None) if parent else None
        head = f"### {n}. {g['theme']}, {g['title']}"
        lines.append(head)
        lines.append("")
        if g["action"] == "keep" or pg is None:
            lines.append(g["statement"])
        else:
            lines.append(f"**{g['action'].capitalize()}.** {g['statement']}")
            lines.append("")
            lines.append(f"Was: ~~{pg['statement']}~~")
            if pg["title"] != g["title"]:
                lines.append(f"Was titled: ~~{pg['theme']}, {pg['title']}~~")
            lines.append("")
            lines.append(f"Reason: {g['reason']}")
        lines.append("")
    return "\n".join(lines)


def render_entry(e, entries):
    parent = next((x for x in entries if x["number"] == e.get("parent")), None)
    md = [TEST_BANNER if SRC["test"] else ""]
    md.append(f"# {e['number']:03d} · {e['title']}\n")
    md.append("| | |\n|---|---|")
    md.append(f"| Kind | {e['kind']} |")
    if e["kind"] != "genesis":
        o = e["organisation"]
        md.append(f"| Tabled by | {o['legal_name']} ({o['kind']}) |")
        md.append(f"| Authorised signer | {e['signer']['name']}, {e['signer']['role']} |")
    else:
        md.append(f"| Tabled by | {e['signer']['name']}, as a resident |")
    if parent:
        md.append(f"| Builds on | {parent['number']:03d} |")
    if e.get("supersedes"):
        md.append(f"| Revises | {e['supersedes']:03d} |")
    md.append(f"| Entered | {e['entered']} |")
    md.append(f"| Status | {e['status']} |")
    md.append(f"| Signable | {'no' if e['kind'] == 'genesis' else 'yes'} |")
    md.append("| Licence | CC BY 4.0 |")
    md.append("")
    if e.get("preamble"):
        md.append(e["preamble"] + "\n")
    md.append("## The Ten\n")
    md.append(goals_table(e, parent))
    if e.get("authors"):
        md.append("## Authors (credits, not signatures)\n")
        for a in e["authors"]:
            md.append(f"- {a['name']}, {a['role']}")
        md.append("")
    if e.get("joined_by"):
        md.append("## Also tabled by\n")
        for j in e["joined_by"]:
            md.append(f"- {j['organisation']}, joined {j['date']}")
        md.append("")
    md.append("## Gates, self-attested by the tabler\n")
    for k, v in e["gates"].items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("Signature counts live in `reviews/`, read at every month-end. "
              "No individual signer appears in this repository.\n")
    base = entry_path(e)
    write(base + ".md", "\n".join(md))
    dump(base + ".json", e)
    return base


def render_review(r):
    md = [TEST_BANNER if SRC["test"] else ""]
    md.append(f"# Reading · {r['period']}\n")
    md.append(f"Cutoff {r['cutoff_at']}. Run {r['ran_at']}.\n")
    md.append(f"Floor: {r['floor']['signatures']} signatures from at least "
              f"{r['floor']['walks']} walks of life.\n")
    if r.get("held"):
        md.append(f"**Held.** {r['hold_reason']}\n")
    md.append("| Entry | Signatures | Walks | Named | Unnamed | Under review | Eligible |")
    md.append("|---|---|---|---|---|---|---|")
    for t in r["tallies"]:
        md.append(f"| {t['entry']:03d} | {t['signatures']} | {t['walks']} | {t['named']} | "
                  f"{t['unnamed']} | {t['under_review']} | {'yes' if t['eligible'] else 'no'} |")
    md.append("")
    lead = r.get("leading_entry")
    md.append(f"**Outcome.** " + (f"Entry {lead:03d} leads for {r['leads_for']}."
                                  if lead else "No leading version yet."))
    md.append("")
    md.append("Spread by walk, per entry:\n")
    for t in r["tallies"]:
        md.append(f"- {t['entry']:03d}: " + ", ".join(f"{w} {c}" for w, c in t["by_walk"].items()))
    md.append("")
    write(f"reviews/{r['period']}.md", "\n".join(md))
    dump(f"reviews/{r['period']}.json", r)


def render_brake(b):
    md = [TEST_BANNER if SRC["test"] else ""]
    md.append(f"# Brake · {b['date']} · {b['kind']}\n")
    md.append("| | |\n|---|---|")
    md.append(f"| Kind | {b['kind']} |")
    if b.get("entry"):
        md.append(f"| Entry | {b['entry']:03d} |")
    md.append(f"| Starts | {b['starts_at']} |")
    md.append(f"| Ends | {b.get('ends_at') or 'on resolution'} |")
    md.append(f"| Recorded by | {b['recorded_by']} |")
    md.append("")
    md.append(f"**Reason.** {b['reason']}\n")
    md.append("The brake slows. It never steers. An admin cannot edit an entry, "
              "change a count, delete anything, run a reading early or pick a version.\n")
    write(f"brake/{b['date']}-{b['kind']}.md", "\n".join(md))
    dump(f"brake/{b['date']}-{b['kind']}.json", b)


def main():
    entries = SRC["entries"]
    paths = {e["number"]: render_entry(e, entries) for e in entries}
    for r in SRC["reviews"]:
        render_review(r)
    for b in SRC["brake"]:
        render_brake(b)
    for s in SRC["settings"]:
        dump(f"settings/{s['effective_from']}.json", s)
    dump("not-admitted.json", SRC["not_admitted"])

    latest = SRC["reviews"][-1] if SRC["reviews"] else None
    index = {
        "test": SRC["test"],
        "repository": SRC["repository"],
        "licence": "CC BY 4.0",
        "generated_from": "tools/source.json",
        "leading_entry": latest["leading_entry"] if latest else None,
        "last_reading": latest["period"] if latest else None,
        "entries": [
            {
                "number": e["number"],
                "kind": e["kind"],
                "title": e["title"],
                "organisation": e["organisation"]["short_name"] if e.get("organisation") else None,
                "parent": e.get("parent"),
                "supersedes": e.get("supersedes"),
                "entered": e["entered"],
                "status": e["status"],
                "signable": e["kind"] != "genesis",
                "path": paths[e["number"]] + ".json",
            }
            for e in entries
        ],
        "reviews": [f"reviews/{r['period']}.json" for r in SRC["reviews"]],
        "brake": [f"brake/{b['date']}-{b['kind']}.json" for b in SRC["brake"]],
        "settings": [f"settings/{s['effective_from']}.json" for s in SRC["settings"]],
    }
    dump("ledger.json", index)
    print("built", len(entries), "entries,", len(SRC["reviews"]), "readings,", len(SRC["brake"]), "brake records")


if __name__ == "__main__":
    main()
