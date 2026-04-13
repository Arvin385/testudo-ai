"""
Scrape courses taught by UMD faculty from Testudo Schedule of Classes.

Usage:
    python scrape_testudo_courses.py                    # test mode: 5 professors
    python scrape_testudo_courses.py --test 100         # test 100 professors
    python scrape_testudo_courses.py --all              # all professors in CSV
    python scrape_testudo_courses.py --name "Kauffman, Christopher" --term 202601
    python scrape_testudo_courses.py --debug --name "Christopher Kauffman"

Term ID format:
    YYYYMM where MM = 01 (Spring), 05 (Summer), 08 (Fall), 12 (Winter)
    Example: 202601 = Spring 2026, 202508 = Fall 2025
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import argparse
import urllib.parse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_URL = "https://app.testudo.umd.edu/soc/search"
CSV_PATH = Path(__file__).parent.parent / "tools" / "umd_faculty.csv"

# Default semesters to search (most recent academic year)
DEFAULT_TERMS = ["202601", "202508"]  # Spring 2026, Fall 2025

# Polite delay range (seconds) between requests
DELAY_MIN = 1.0
DELAY_MAX = 2.0

# Retry config for 400/5xx errors
MAX_RETRIES = 2
RETRY_DELAY = 5.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://app.testudo.umd.edu/soc/",
}


# ---------------------------------------------------------------------------
# Name parsing & standardization
# ---------------------------------------------------------------------------

def parse_name(raw: str) -> dict:
    """
    Parse a name string into components.
    Returns dict with keys: first, middle (may be ""), last, original, standardized.

    Handles:
        "Kauffman, Christopher"    -> first=Christopher, last=Kauffman
        "Christopher Kauffman"     -> first=Christopher, last=Kauffman
        "Sanner, Robert M."        -> first=Robert, middle=M., last=Sanner
        "C. Anton Rytting"         -> first=C. Anton, last=Rytting  (tricky)
        "Cornelia Van der Weele"   -> first=Cornelia, last=Van der Weele
        "Hal Daumé III"            -> first=Hal, last=Daumé, suffix=III
        "A. Udaya Shankar"         -> first=A. Udaya, last=Shankar
        "G.W. (Pete) Stewart"      -> first=G.W. (Pete), last=Stewart
    """
    raw = raw.strip()
    result = {"original": raw, "first": "", "middle": "", "last": "", "suffix": ""}

    # Suffixes to strip
    suffix_pattern = re.compile(r'\s+(III|IV|Jr\.?|Sr\.?|II)\s*$', re.I)
    m = suffix_pattern.search(raw)
    if m:
        result["suffix"] = m.group(1)
        raw = raw[:m.start()].strip()

    if "," in raw:
        # "Last, First Middle" format
        parts = raw.split(",", 1)
        result["last"] = parts[0].strip()
        rest = parts[1].strip().split()
        if rest:
            result["first"] = rest[0]
            result["middle"] = " ".join(rest[1:]) if len(rest) > 1 else ""
    else:
        # "First (Middle...) Last" format
        # Challenge: multi-word last names like "Van der Weele", "De Floriani"
        parts = raw.split()
        if len(parts) == 1:
            result["last"] = parts[0]
        elif len(parts) == 2:
            result["first"] = parts[0]
            result["last"] = parts[1]
        else:
            # Heuristic: last name starts at the last capitalized word
            # that isn't a common middle-name pattern.
            # Multi-word last names: Van, De, Del, Der, Di, La, Le, Von, Al, El
            multi_prefixes = {"van", "de", "del", "der", "di", "la", "le", "von",
                              "al", "el", "bin", "ibn", "da", "dos", "das", "du"}

            # Walk backwards from the end to find where last name starts
            last_start = len(parts) - 1
            while last_start > 1 and parts[last_start - 1].lower() in multi_prefixes:
                last_start -= 1

            # Everything before last_start is first+middle, the rest is last
            first_middle = parts[:last_start]
            result["last"] = " ".join(parts[last_start:])

            if len(first_middle) == 1:
                result["first"] = first_middle[0]
            elif len(first_middle) >= 2:
                result["first"] = first_middle[0]
                result["middle"] = " ".join(first_middle[1:])

    return result


def standardize_name(parsed: dict) -> str:
    """
    Build standardized 'First (Middle) Last (Suffix)' display name.
    """
    parts = []
    if parsed["first"]:
        parts.append(parsed["first"])
    if parsed["middle"]:
        parts.append(parsed["middle"])
    if parsed["last"]:
        parts.append(parsed["last"])
    if parsed["suffix"]:
        parts.append(parsed["suffix"])
    return " ".join(parts)


def generate_testudo_queries(parsed: dict) -> list[str]:
    """
    Generate Testudo search strings (Last, First) to try, in priority order.
    Returns multiple variants to handle name ambiguities.

    Testudo only accepts "Last, First" -- no middle names or initials.
    """
    queries = []
    last = parsed["last"]
    first = parsed["first"]
    middle = parsed["middle"]

    if not last or not first:
        # Can't construct a query without both parts
        if last:
            queries.append(last)
        return queries

    # Clean initials: strip periods from single-letter initials
    def clean_initial(s):
        return s.replace(".", "").strip()

    # Check if first name looks like an initial (e.g., "C." or "A" or "P.K.")
    first_clean = clean_initial(first)
    first_is_initial = len(first_clean) <= 2 and ("." in first or len(first) == 1)
    # Also catch multi-initials like "G.W." or "P.K."
    if re.match(r'^[A-Z]\.[A-Z]\.?$', first.replace(" ", "")):
        first_is_initial = True

    # Query 1: "Last, First" (most common case)
    queries.append(f"{last}, {first}")

    # If first name is an initial and there's a middle name, the "real" first
    # name is probably the middle. e.g., "C. Anton Rytting" -> try "Rytting, Anton"
    if first_is_initial and middle:
        # Strip parenthetical from middle before using as first name
        middle_clean = re.sub(r'\(.*?\)\s*', '', middle).strip()
        if middle_clean:
            middle_parts = middle_clean.split()
            queries.append(f"{last}, {middle_parts[0]}")

    # If there's a middle initial, try without it (already handled by using
    # just first name above, but also try first+middle in case Testudo stores it)
    if middle and not first_is_initial:
        # Try "Last, First Middle" in case Testudo uses full name
        queries.append(f"{last}, {first} {middle}")

    # Strip periods from first name for a cleaner query
    if "." in first:
        cleaned = first.replace(".", "").strip()
        if cleaned != first:
            queries.append(f"{last}, {cleaned}")

    # Remove parenthetical nicknames: "G.W. (Pete)" -> try "Stewart, Pete"
    paren_match = re.search(r'\((\w+)\)', parsed.get("original", ""))
    if paren_match:
        nickname = paren_match.group(1)
        queries.append(f"{last}, {nickname}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique


# ---------------------------------------------------------------------------
# HTTP & Parsing
# ---------------------------------------------------------------------------

def build_search_url(instructor: str, term_id: str) -> str:
    """Build the Testudo SOC search URL for a given instructor and term."""
    params = {
        "courseId": "",
        "sectionId": "",
        "termId": term_id,
        "_openSectionsOnly": "on",
        "creditCompare": "",
        "credits": "",
        "courseLevelFilter": "ALL",
        "instructor": instructor,
        "_facetoface": "on",
        "_blended": "on",
        "_online": "on",
        "courseStartCompare": "",
        "courseStartHour": "",
        "courseStartMin": "",
        "courseStartAM": "",
        "courseEndHour": "",
        "courseEndMin": "",
        "courseEndAM": "",
        "teachingCenter": "ALL",
        "_classDay1": "on",
        "_classDay2": "on",
        "_classDay3": "on",
        "_classDay4": "on",
        "_classDay5": "on",
    }
    return BASE_URL + "?" + urllib.parse.urlencode(params)


def fetch_page(url: str, session: requests.Session) -> requests.Response | None:
    """Fetch a page with retry logic for 400/5xx errors."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 400:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
            elif resp.status_code >= 500:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                return None
            else:
                return None
        except requests.RequestException as e:
            print(f"    [ERROR] Request failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


def parse_courses(html: str) -> list[str]:
    """
    Parse Testudo search results HTML and extract course IDs + titles.

    Testudo HTML structure:
        <div class="course" id="CMSC216">
            <div class="course-id">CMSC216</div>
            <span class="course-title">Introduction to Computer Systems</span>
        </div>

    Returns: ["CMSC216: Introduction to Computer Systems", ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    courses = []

    for div in soup.find_all("div", class_="course"):
        course_id_el = div.find("div", class_="course-id")
        course_title_el = div.find("span", class_="course-title")

        if course_id_el and course_title_el:
            cid = course_id_el.get_text(strip=True)
            title = course_title_el.get_text(strip=True)
            course_str = f"{cid}: {title}"
            if course_str not in courses:
                courses.append(course_str)

    return courses


def scrape_professor(name: str, terms: list[str], session: requests.Session,
                     verbose: bool = True) -> tuple[list[str], str | None]:
    """
    Query Testudo for all courses taught by a professor across given terms.
    Tries multiple name variants.

    Returns: (deduplicated course list, the query string that worked or None)
    """
    parsed = parse_name(name)
    queries = generate_testudo_queries(parsed)

    if not queries:
        if verbose:
            print(f"    [SKIP] Could not generate search query for: {name}")
        return [], None

    all_courses = []
    seen = set()
    winning_query = None

    for query in queries:
        found_any = False

        for term in terms:
            url = build_search_url(query, term)
            if verbose:
                print(f"    Trying '{query}' for {term}...")

            resp = fetch_page(url, session)
            if resp is None:
                if verbose:
                    print(f"      -> Request failed")
                continue

            if "No courses matched your search filters" in resp.text:
                if verbose:
                    print(f"      -> No courses")
                # Polite delay
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
                continue

            courses = parse_courses(resp.text)
            if courses:
                found_any = True
                winning_query = query
                for c in courses:
                    if c not in seen:
                        seen.add(c)
                        all_courses.append(c)
                if verbose:
                    print(f"      -> {len(courses)} course(s)")

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        # If first query variant found results, don't try other variants
        if found_any:
            break

    return all_courses, winning_query


def dump_html_structure(name: str, term: str):
    """Debug helper: fetch one page and print the HTML structure around courses."""
    parsed = parse_name(name)
    queries = generate_testudo_queries(parsed)
    query = queries[0] if queries else name
    url = build_search_url(query, term)
    session = requests.Session()
    resp = fetch_page(url, session)
    if resp is None:
        print("Failed to fetch page")
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    print("=== Elements with 'course' in class ===")
    for el in soup.find_all(class_=re.compile(r"course", re.I)):
        print(f"  Tag: <{el.name}> Class: {el.get('class')} ID: {el.get('id')}")
        txt = el.get_text(strip=True)[:200]
        print(f"    Text: {txt}")
        print()

    print("=== Heading tags (h1-h4) ===")
    for tag in ["h1", "h2", "h3", "h4"]:
        for el in soup.find_all(tag):
            classes = el.get("class", [])
            print(f"  <{tag} class={classes}> {el.get_text(strip=True)[:100]}")


def load_faculty_csv() -> list[dict]:
    """Load the faculty CSV and return list of row dicts."""
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape Testudo for faculty courses")
    parser.add_argument("--name", type=str, help="Single professor name to search")
    parser.add_argument("--term", type=str, help="Single term ID (e.g. 202601)")
    parser.add_argument("--terms", type=str, nargs="+", help="List of term IDs")
    parser.add_argument("--all", action="store_true", help="Run for all faculty in CSV")
    parser.add_argument("--debug", action="store_true", help="Dump HTML structure")
    parser.add_argument("--test", type=int, default=5,
                        help="Number of professors to test (default: 5)")
    args = parser.parse_args()

    terms = DEFAULT_TERMS
    if args.term:
        terms = [args.term]
    elif args.terms:
        terms = args.terms

    # Debug mode
    if args.debug:
        name = args.name or "Christopher Kauffman"
        print(f"=== DEBUG: HTML structure for {name}, term {terms[0]} ===\n")
        dump_html_structure(name, terms[0])
        return

    # Single professor mode
    if args.name:
        session = requests.Session()
        parsed = parse_name(args.name)
        std_name = standardize_name(parsed)
        print(f"Searching for: {args.name}")
        print(f"Standardized: {std_name}")
        print(f"Queries to try: {generate_testudo_queries(parsed)}")
        print(f"Terms: {terms}\n")
        courses, winning_q = scrape_professor(args.name, terms, session)
        print(f"\n--- Results for {std_name} ---")
        if winning_q:
            print(f"  Matched as: {winning_q}")
        if courses:
            for c in courses:
                print(f"  {c}")
        else:
            print("  (no courses found)")
        return

    # Batch mode: load CSV and iterate
    faculty = load_faculty_csv()
    print(f"Loaded {len(faculty)} faculty from CSV")
    print(f"Terms: {terms}\n")

    if not args.all:
        # Deterministic sample for reproducibility
        random.seed(42)
        sample = random.sample(faculty, min(args.test, len(faculty)))
        faculty = sample

    print(f"Processing {len(faculty)} professor(s)...\n")
    session = requests.Session()

    results = {}         # name -> courses list
    name_mapping = {}    # original name -> standardized name
    match_queries = {}   # name -> query that worked
    errors = []          # names that failed
    no_results = []      # names with 0 courses

    for i, row in enumerate(faculty):
        name = row["Name"].strip()
        dept = row.get("department", "?")

        # Skip garbage entries
        if not name or name.startswith("#"):
            continue

        parsed = parse_name(name)
        std_name = standardize_name(parsed)
        name_mapping[name] = std_name

        print(f"[{i+1}/{len(faculty)}] {name} -> {std_name} ({dept})")

        courses, winning_q = scrape_professor(name, terms, session, verbose=True)

        if courses:
            results[name] = courses
            match_queries[name] = winning_q
            print(f"  => FOUND {len(courses)}: {', '.join(courses)}")
        else:
            no_results.append(name)
            print(f"  => No courses found")
        print()

    # ---- Summary ----
    total = len(faculty)
    found = len(results)
    not_found = len(no_results)

    print("=" * 70)
    print(f"SUMMARY: {found}/{total} professors had courses on Testudo")
    print(f"         {not_found} had no courses found")
    print("=" * 70)

    print(f"\n--- Name standardization samples ---")
    changed = [(orig, std) for orig, std in name_mapping.items() if orig != std]
    for orig, std in changed[:20]:
        print(f"  '{orig}' -> '{std}'")
    if len(changed) > 20:
        print(f"  ... and {len(changed) - 20} more")

    print(f"\n--- Professors with courses ---")
    for name, courses in results.items():
        std = name_mapping.get(name, name)
        q = match_queries.get(name, "?")
        print(f"\n  {std} (searched: '{q}'):")
        for c in courses:
            print(f"    {c}")

    print(f"\n--- Professors with NO courses (first 30) ---")
    for name in no_results[:30]:
        std = name_mapping.get(name, name)
        parsed = parse_name(name)
        queries = generate_testudo_queries(parsed)
        print(f"  {std} (tried: {queries})")


if __name__ == "__main__":
    main()
