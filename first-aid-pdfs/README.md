# Offline First Aid PDF Library

A curated set of reputable, freely available first aid references, intended to be
downloaded and stored offline (e.g. on a flash drive) for use when there is no
internet connection.

> **Note:** This directory contains the source list and download scripts, not the
> PDFs themselves. Run one of the scripts below on a machine with normal internet
> access to fetch everything.

## Quick start

**Linux / macOS:**

```bash
cd first-aid-pdfs
./download.sh            # downloads into ./downloads/
```

**Windows (PowerShell):**

```powershell
cd first-aid-pdfs
.\download.ps1           # downloads into .\downloads\
```

Each script retries failed downloads, verifies every file actually starts with the
`%PDF` magic bytes (so you don't end up with an HTML error page saved as `.pdf`),
and prints a summary. Copy the resulting `downloads/` folder to your flash drive.

## The sources

| File | Publisher | What it is |
|---|---|---|
| `ifrc-first-aid-guidelines-2025.pdf` | IFRC (Red Cross / Red Crescent) | International First Aid, Resuscitation and Education Guidelines 2025 — the evidence-based global reference behind most national first aid curricula. |
| `ifrc-first-aid-guidelines-2020.pdf` | IFRC | The 2020 edition of the same guidelines (kept as a fallback/alternate). |
| `us-army-first-aid-tc-4-02-1.pdf` | U.S. Department of the Army | Training Circular 4-02.1 "First Aid" — the Army's first aid manual for non-medical personnel. U.S. government work, public domain. |
| `red-cross-first-aid-cpr-aed-ready-reference.pdf` | American Red Cross | The quick-reference handout for adult first aid / CPR / AED given to training participants. |
| `sja-first-aid-reference-guide.pdf` | St John Ambulance (UK) | Compact first aid reference guide covering common scenarios. |
| `sja-first-aid-guide-supplement-2021.pdf` | St John Ambulance (UK) | Updated guidance supplement on first aid scenarios. |
| `who-psychological-first-aid.pdf` | World Health Organization | "Psychological First Aid: Guide for Field Workers" — supporting people in the immediate aftermath of crisis events. |
| `where-there-is-no-doctor.pdf` | Hesperian Health Guides | The classic village health care handbook — far broader than first aid, invaluable when professional care is out of reach. Hesperian permits free non-commercial digital distribution. |

Direct URLs (including fallbacks) live in `sources.txt`, which both scripts read.

## Also worth grabbing manually

These publishers gate their best material behind a landing page rather than a
stable direct link — visit in a browser and download:

- **Hesperian HealthWiki / chapter downloads** — <https://store.hesperian.org/products/where-there-is-no-doctor> (newest edition, free chapter PDFs)
- **American Red Cross brochure downloads** — <https://www.redcross.org/take-a-class/organizations/education/brochure-downloads>
- **St John Ambulance accessible resources** — <https://www.sja.org.uk/get-advice/accessible-first-aid-resources/>

## Licensing note

These documents remain copyrighted by their publishers (except the U.S. Army
manual, which is public domain). All are distributed free of charge by their
publishers and are listed here for personal offline reference. Don't resell or
rehost them commercially.

## Disclaimer

These references are no substitute for hands-on first aid training or
professional medical care. Consider a certified course from your local Red
Cross/Red Crescent society, St John Ambulance, or equivalent.
