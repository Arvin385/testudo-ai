# Data Cleaning — Known Issues & Future Tasks

## Overview

This document tracks data quality issues in `tools/umd_faculty_master.csv` and the underlying `.db` files. Use this as a backlog when doing cleaning work.

---

## Priority 1: Department Name Normalization

The `department` column has inconsistent naming from different source databases. The same department appears under multiple strings.

### Electrical & Computer Engineering (48+ faculty)
```
Electrical and Computer Engineering                          ← cmsc/amsc
Electrical & Computer Engineering                            ← clark
ECE and ISR                                                  ← amsc
Electrical and Computer Engineering, UMIACS                  ← amsc
Electrical and Computer Engineering, The Institute for Systems Research
Electrical and Computer Engineering, Maryland Cybersecurity Center, UMIACS
```
**Target:** Primary department = `Electrical & Computer Engineering`

### Civil & Environmental Engineering (23+ faculty)
```
Civil and Environmental Engineering                          ← cmsc
Civil & Environmental Engineering                            ← clark
Civil and Environmental Engineering, Center for Risk and Reliability
```
**Target:** Primary department = `Civil & Environmental Engineering`

### Chemical & Biomolecular Engineering (17+ faculty)
```
Chemical and Biomolecular Engineering, Maryland Energy Innovation Institute
Chemical & Biomolecular Engineering                          ← clark
Chemical and Biomolecular Engineering                        ← cmsc
```
**Target:** Primary department = `Chemical & Biomolecular Engineering`

### Similar issues exist for:
- `Atmospheric & Oceanic Science` vs `Atmospheric and Oceanic Science` vs `Atmosphere and Oceanic Science`
- `Decision, Operations & Information Technologies` vs `Department of Decision, Operations, & Information Technologies` vs `DO&IT`
- `Bioengineering` vs `Fischell Department of Bioengineering` vs `Biocomputational Engineering, Fischell Department of Bioengineering`
- `Chemistry` vs `Chemistry & Biochemistry`
- `Epidemiology and Biostatistics` vs `Epidemiology & Biostatistics`

### Suggested approach
- Add a `normalize_department()` function to `consolidate_to_csv.py`
- Map variants to canonical names
- Consider splitting into `primary_department` and `affiliations` columns
- Alternatively, keep the first comma-separated value as primary and the rest as affiliations

---

## Priority 2: Low-Coverage Columns

### `courses_taught` — 10.6% (99/938)
- Only Physics (from CMNS scraper) and Clark Engineering departments have teaching data in their profiles
- CMSC, Smith, and other CMNS departments don't expose course lists on profile pages
- **Possible enrichment:** Cross-reference with Testudo schedule data or UMD Schedule of Classes API

### `publications` — 11.1% (104/938)
- Only Clark Engineering profiles have a `PUBLICATIONS` section in `extra_info`
- CMNS profiles rarely include publication lists directly
- **Possible enrichment:** Google Scholar scraping or PubMed API lookups by faculty name

### `phone` — 56.7% (532/938)
- Many profiles simply don't list phone numbers
- Some numbers include labels like `office: 301-...` or `lab: 301-...`
- **Cleaning task:** Normalize phone format (strip labels, standardize to `301-405-XXXX`)

---

## Priority 3: Field Content Cleaning

### `courses_taught` remaining issues
- Some entries include semester/year annotations: `ENCE215: Engineering for Sustainability (Spring '15, '16...)`
  - Decide: strip the annotations, or keep for context?
- Cross-listed courses with 3+ codes get dropped: `BIOE 489T/ BIOE689E/ CHBE474- Title`
  - The `_extract_course` regex only handles `CODE/CODE` patterns (2 codes max)
- Pure prose entries produce empty output (~19 faculty had text but no extractable course IDs)

### `key_expertise` formatting
- Currently a raw dump of `bio` + research sections
- The OneClique CSV uses a summarized format: `"Expertise in X. UMD Professor; mentors in Y."`
- **Future task:** Summarize or restructure to match that style (possibly with LLM assistance)

### `office` inconsistencies
- Some entries have just a room number: `3118 Physical Sciences Complex`
- Others have building abbreviations: `1321 A.V. Williams Bldg.`
- No standard format across departments

### `Name` format
- Clark uses `Last, First M.` format
- CMNS uses `First Last` format
- **Cleaning task:** Normalize to one format consistently

---

## Priority 4: Missing Departments

Departments not yet scraped (from `SCRAPING_ROADMAP.md`):
- College of Education
- School of Public Health
- iSchool (College of Information Studies)
- College of Arts and Humanities
- Philip Merrill College of Journalism
- School of Public Policy
- College of Agriculture and Natural Resources
- School of Architecture, Planning and Preservation

---

## Validation Checks

Run these after any cleaning pass:

```python
# Quick validation script
import csv
with open('tools/umd_faculty_master.csv', 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# 1. No duplicate emails
emails = [r['email'].lower().strip() for r in rows if r['email'].strip()]
assert len(emails) == len(set(emails)), f"Duplicate emails: {len(emails) - len(set(emails))}"

# 2. All courses in CODE: Name format
import re
for r in rows:
    for line in (r['courses_taught'] or '').split('\n'):
        if line.strip():
            assert re.match(r'^[A-Z]{2,6}\d{3}', line), f"Bad course format: {line!r} for {r['Name']}"

# 3. Coverage hasn't regressed
for col, min_pct in [('email', 99), ('department', 99), ('Name', 100)]:
    filled = sum(1 for r in rows if (r[col] or '').strip())
    pct = filled / len(rows) * 100
    assert pct >= min_pct, f"{col} coverage dropped to {pct:.1f}%"
```
