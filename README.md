# Bermuda 10 · Test ledger

> **Test ledger.** Every organisation, entry, signature count and reading in this repository is invented to rehearse the process. Nothing here is on the record. The real ledger is `bermuda10/ledger`.

This repository has the same layout, rules and file formats as the real ledger, so the website, the admin tools and the month-end reading can be exercised end to end before any real organisation tables a version.

## What the ledger is

Bermuda 10 asks one question: what would have to be true for Bermuda to be the best place to live on Earth by 2050? The answers live as an open, append-only ledger. Organisations table their answers, copied or changed, and co-sign one another's from the second entry on. Residents sign the answer they stand behind. At every month-end the ledger is read and records who backs what. It declares no winner. Bermuda 10 keeps the record and counts. It never tables an answer, never co-signs one and never chooses one.

## Layout

```
index.json                  index of everything below, what the website reads first
entries/001-genesis.md      one entry per version, human readable
entries/001-genesis.json    the same entry, machine readable
readings/2026-10.md + .json one record per month-end reading
brake/                      every use of the brake, with its reason
settings/                   thresholds, one file per change, with effective date
not-admitted.json           running count of submissions not admitted, by reason
tools/source.json           the single source the files above are built from
tools/build.py              the builder, run it after editing source.json
```

## Rules in brief

- Genesis (001) is the founder's draft, frozen, and can never be signed or co-signed by anyone. An organisation that agrees with it tables its own copy and keeps all ten.
- Only organisations table. Political parties may not table. From the second entry on, organisations co-sign tabled answers and residents sign them, one signature each.
- An answer builds on an earlier one or starts its own line. Nothing published is edited or deleted. A revision is a new numbered entry.
- Read at 23:59 Atlantic/Bermuda on the last day of every month. A reading records backing and declares nothing. There is no leading version until a convergence rule is written with the participants and published.
- The brake slows and never steers. Every use is recorded here with a written reason.
- No individual signer, named or unnamed, ever appears in this repository. Counts and spread by walk only. Organisations that co-sign appear by name, as they agreed.
- Text is licensed CC BY 4.0.

## How the website reads it

The site fetches `index.json`, then the `.json` file for each entry, reading or brake record it needs. If the site and this repository ever differ, the repository is right.

## Regenerating

```
python3 tools/build.py
```

Edit `tools/source.json`, run the builder, commit everything. The `.md` and `.json` files are never edited by hand.
