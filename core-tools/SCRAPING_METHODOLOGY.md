# Web Scraping Methodology for UMD Faculty Data Collection

## Overview
This document outlines the systematic approach for developing web scrapers to collect faculty information from UMD department websites. This methodology has been successfully applied to Physics, Biology, Mathematics, and AMSC departments.

---

## Phase 1: Exploration & Discovery

### Step 1.1: Identify Target URLs
- Start with department main page or faculty directory
- Use `WebFetch` tool to verify page exists and get initial structure overview
- Example:
  ```python
  WebFetch(url="https://dept.umd.edu/people/faculty",
           prompt="Does this page exist? How many faculty? What's the structure?")
  ```

### Step 1.2: Download Main Listing Page
- Use Playwright to download the faculty listing page
- Save both HTML and screenshot for analysis
- Code template:
  ```python
  from playwright.sync_api import sync_playwright

  with sync_playwright() as p:
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      page.goto(TARGET_URL, wait_until='networkidle')
      time.sleep(2-3)  # Allow dynamic content to load

      html = page.content()
      with open('dept_faculty_listing.html', 'w', encoding='utf-8') as f:
          f.write(html)

      page.screenshot(path='dept_faculty_listing.png', full_page=True)
      browser.close()
  ```

---

## Phase 2: Structure Analysis

### Step 2.1: Identify Faculty Entry Patterns
Analyze the HTML to find repeating patterns that represent individual faculty:
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'html.parser')

# Try multiple discovery strategies:
# 1. Look for email links (most reliable indicator)
email_links = soup.find_all('a', href=lambda x: x and 'mailto:' in x)

# 2. Look for common class patterns
faculty_divs = soup.find_all('div', class_=lambda x: x and
    any(term in str(x).lower() for term in ['person', 'faculty', 'profile', 'team']))

# 3. Look for specific structural patterns (varies by site)
# Examples:
# - Physics/Math: div.catItemExtraFields
# - Biology: div.team-name
# - AMSC: accordion buttons with data-rlta-element="button"
```

### Step 2.2: Extract Sample Entries
Select 5 random faculty entries to analyze:
```python
import random
random.seed(42)
samples = random.sample(faculty_list, min(5, len(faculty_list)))

# For each sample, extract and document:
# - Name location
# - Email location
# - Title location
# - Profile URL pattern
# - Any additional fields
```

### Step 2.3: Document Field Locations
Create a mapping of where each field is located:
```
FIELD LOCATION MAP:
- Name: div.team-name > a
- Email: a[href^="mailto:"]
- Title: div.field--name-field-team-position
- Profile URL: div.team-name > a[href]
- Phone: div containing "Phone:"
```

---

## Phase 3: Profile Enrichment Strategy

### Step 3.1: Download Sample Profile Pages
If faculty have individual profile pages, download 3-5 samples:
```python
# Select profiles from different categories (current faculty, emeritus, etc.)
test_profiles = [
    ('Name1', 'https://dept.umd.edu/people/faculty/person1'),
    ('Name2', 'https://dept.umd.edu/people/faculty/person2'),
]

for name, url in test_profiles:
    page.goto(url, wait_until='networkidle')
    html = page.content()
    with open(f'profile_{name}.html', 'w', encoding='utf-8') as f:
        f.write(html)
```

### Step 3.2: Analyze Profile Structure
Identify sections containing rich biographical data:
```python
# Common sections to look for:
# 1. Biography/Research Interests - Main descriptive text
# 2. CV/Curriculum Vitae link
# 3. Personal/Lab website
# 4. Research areas
# 5. Publications
# 6. Teaching courses
# 7. Awards/Honors
# 8. Education
# 9. News/Achievements
# 10. Graduate program affiliations

# Document the HTML structure for each:
# - Physics: Uses tabs (div#biography, div#research, div#teaching, div#news)
# - Biology: Uses div.field--name-body with multiple h3 sections
# - Others: Varies, must analyze
```

### Step 3.3: Create Extraction Strategy Document
Write down the extraction plan:
```markdown
## Extraction Strategy for [Department]

1. **Biography**: [location in HTML]
2. **CV Link**: [selector]
3. **Website**: [selector]
4. **Research**: [selector]
5. **Teaching**: [selector]
...

Store in database:
- bio field: Main research description
- extra_info field: All other sections with clear headers
```

---

## Phase 4: Script Development

### Step 4.1: Create Database Model
Use consistent schema across all departments:
```python
class CMNSFaculty(Base):
    __tablename__ = "cmns_faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    title = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    profile_url = Column(String(255))
    source_department = Column(String(255))
    bio = Column(Text)  # Main research description
    extra_info = Column(Text)  # Additional sections with headers
```

### Step 4.2: Write Helper Function for Profile Scraping
```python
def scrape_profile_details(page, profile_url):
    """
    Visit faculty profile and extract biographical information.

    Returns:
        dict: {'bio': str, 'extra_info': str}
    """
    result = {'bio': '', 'extra_info': ''}

    try:
        page.goto(profile_url, wait_until='networkidle', timeout=10000)
        time.sleep(1)

        soup = BeautifulSoup(page.content(), 'html.parser')

        extra_sections = []

        # Extract each section based on discovered structure
        # Add clear section headers for extra_info

        # Example for CV link:
        cv_link = soup.find('a', href=lambda x: x and '/cv/' in x.lower())
        if cv_link:
            extra_sections.append(f"CURRICULUM VITAE:\n{cv_link.get('href')}")

        # Combine with headers
        result['extra_info'] = "\n\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error: {e}")
        # Don't fail entire process

    return result
```

### Step 4.3: Write Main Scraping Function
```python
def scrape_dept_enriched():
    """Main scraping function with enrichment."""

    # 1. Setup database (test_faculty.db for testing)
    engine = create_engine("sqlite:///../tools/test_faculty.db")

    # 2. Download main listing page
    # 3. Parse to find all faculty entries
    # 4. For each faculty:
    #    a. Extract basic info from listing
    #    b. If profile_url exists, visit and enrich
    # 5. Save to database
    # 6. Return statistics
```

---

## Phase 5: Testing & Iteration

### Step 5.1: Test on Small Sample
**CRITICAL**: Always test on 5-10 faculty first with test_faculty.db
```python
# In script, add testing limits:
faculty_list = faculty_list[:10]  # Test on first 10
logging.info(f"Testing with first {len(faculty_list)} entries")
```

### Step 5.2: Run Test and Analyze Output
```bash
cd core-tools && ../.venv/Scripts/python.exe scrape_dept_enriched.py
```

Check the summary output:
- How many faculty successfully scraped?
- What percentage have bio vs extra_info?
- Are any fields completely empty? (might indicate selector issue)
- Sample one full entry to verify data quality

### Step 5.3: Debug Common Issues

**Issue: No bio/extra_info extracted**
- Profile structure might be different than expected
- Use browser developer tools or save HTML samples
- Check if there are multiple divs with same class (need to filter)
  ```python
  # Example fix: Find the RIGHT div among multiple
  all_divs = soup.find_all('div', class_='content')
  content_div = None
  for div in all_divs:
      if div.find('h3'):  # Has headings = actual content
          content_div = div
          break
  ```

**Issue: Some faculty have data, others don't**
- Different faculty types have different profile structures
- Check if current faculty vs emeritus/affiliate have different pages
- Add conditional logic or accept that not all will have full profiles

**Issue: Indentation errors or syntax errors**
- Read the file back with the Read tool before editing
- Make sure to preserve indentation when using Edit tool
- Test immediately after each edit

### Step 5.4: Iterate Until Test Succeeds
- Fix one issue at a time
- Re-test after each fix
- Document any edge cases discovered

---

## Phase 6: Full Deployment

### Step 6.1: Switch to Production Database
```python
# Change from:
engine = create_engine("sqlite:///../tools/test_faculty.db")

# To:
engine = create_engine("sqlite:///../tools/cmns_faculty.db")
```

### Step 6.2: Remove Testing Limits
```python
# Remove lines like:
# faculty_list = faculty_list[:10]
# logging.info(f"Testing with...")

# Keep:
logging.info(f"Processing all {len(faculty_list)} entries")
```

### Step 6.3: Run Full Scrape
```bash
cd core-tools && ../.venv/Scripts/python.exe scrape_dept_enriched.py
```

Monitor progress:
- Estimated time: ~2 seconds per profile with enrichment
- 100 faculty ≈ 3-4 minutes
- 200 faculty ≈ 6-7 minutes

### Step 6.4: Verify Results
Check final summary statistics:
- Total faculty count matches expectations
- Bio coverage percentage (typically 30-50% have full profiles)
- Extra info coverage (should be higher, 70-90%)
- Sample a few entries manually to verify quality

---

## Data Structure Standards

### Bio Field
- Contains main research description/interests
- Should be 200-2000 characters typically
- Plain text, cleaned of HTML

### Extra Info Field
- Formatted with clear section headers
- Each section separated by `\n\n`
- Format:
  ```
  SECTION NAME:
  Content here

  ANOTHER SECTION:
  - List item 1
  - List item 2
  ```

### Section Header Standards
Use these consistent headers:
- `CURRICULUM VITAE:` - CV links
- `PERSONAL WEBSITE:` / `LAB WEBSITE:` - External URLs
- `RESEARCH:` - Research areas, publications
- `TEACHING:` - Courses taught
- `NEWS:` - Professional achievements
- `AWARDS:` - Honors and awards
- `EDUCATION:` - Degrees
- `GRADUATE PROGRAM AFFILIATIONS:` - Program memberships
- `OFFICE:` / `CONTACT:` - Location/phone info

---

## Common Patterns by Site Type

### Pattern A: Accordion/Tabs (Physics-style)
- JavaScript tabs or accordions with IDs
- Look for: `div#biography`, `div#research`, etc.
- Profile URL structure: `/people/faculty/category/item/ID-name.html`

### Pattern B: Single Page with Sections (Biology-style)
- All content in one `div.field--name-body`
- H3 headings separate sections
- Multiple divs with same class - need to find the one with headings

### Pattern C: Inline Data (AMSC-style)
- All info on listing page, no separate profiles
- Use accordion panels or collapsible sections
- Look for `data-rlta-element` or similar attributes

### Pattern D: K2/Joomla (Some UMD sites)
- `div.catItemExtraFields` for contact info
- Separate profile pages linked from main listing
- Structured fields with regex-parseable patterns

---

## Troubleshooting Guide

### Problem: Page not loading / timeout
```python
# Increase timeout and add explicit waits
page.goto(url, wait_until='networkidle', timeout=15000)
page.wait_for_selector('div.content', timeout=5000)
time.sleep(2-3)
```

### Problem: JavaScript-heavy pages (AJAX loading)
```python
# Wait for specific elements
page.wait_for_selector('div.faculty-card')
# Or wait for network idle
page.wait_for_load_state('networkidle')
# Scroll to trigger lazy loading
page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
```

### Problem: Email protection/obfuscation
- Look for `cloaked_email` classes
- Check for JavaScript email decoding
- Some sites store email in data attributes

### Problem: Relative URLs
```python
# Always convert to absolute
if href.startswith('http'):
    full_url = href
else:
    full_url = f'https://department.umd.edu{href}'
```

---

## Testing Checklist

Before full deployment, verify:
- [ ] Tested on 10 faculty samples
- [ ] Bio extraction working (if profiles exist)
- [ ] Extra info extraction working
- [ ] All emails collected (99%+ coverage expected)
- [ ] Profile URLs are valid and absolute
- [ ] No Python syntax/indentation errors
- [ ] Database saves without errors
- [ ] Summary statistics look reasonable
- [ ] Sample entries manually reviewed for quality

---

## Performance Notes

- **Speed**: ~2 seconds per faculty with profile enrichment
- **Politeness**: Include 1-2 second delays between requests
- **Timeout**: Use 10-second timeout for individual profiles
- **Error handling**: Always use try-except to avoid failing entire scrape
- **Logging**: Use logging.debug() for profile errors (don't clutter output)

---

## File Organization

```
core-tools/
├── scrape_dept_enriched.py          # Main enriched scraper
├── scrape_dept_basic.py              # Basic listing only (if needed)
├── dept_faculty_listing.html        # Downloaded listing page
├── dept_profile_sample_*.html       # Sample profiles for analysis
├── dept_extraction_strategy.txt     # Documented extraction plan
├── dept_faculty_entries.json        # Parsed entries for testing
└── dept_samples_preview.txt         # Human-readable samples

tools/
├── cmns_faculty.db                  # Production database
├── test_faculty.db                  # Testing database
├── dept_faculty.db                  # Department-specific DB (if separated)
```

---

## Example: Complete Workflow for New Department

```bash
# 1. Exploration
WebFetch("https://newdept.umd.edu/people")

# 2. Download listing
python -c "download_main_page()"

# 3. Analyze structure
python -c "analyze_structure()"

# 4. Download sample profiles (3-5)
python -c "download_samples()"

# 5. Create extraction strategy document
vim newdept_extraction_strategy.txt

# 6. Write scraper
vim scrape_newdept_enriched.py

# 7. Test on 10 faculty
python scrape_newdept_enriched.py  # (with [:10] limit)

# 8. Debug and iterate
# Review output, fix issues, re-test

# 9. Full deployment
python scrape_newdept_enriched.py  # (remove limit, switch to production DB)

# 10. Verify results
# Check summary, sample entries, database
```

---

## Success Metrics

A successful scrape should achieve:
- **Email coverage**: 95%+ (some emeritus faculty may lack emails)
- **Bio coverage**: 30-60% (depends on department's profile completeness)
- **Extra info coverage**: 70-90%
- **Profile URL coverage**: 90%+ (for departments with profile pages)
- **Data quality**: Manual review of 5-10 entries shows accurate, well-formatted data

---

## Notes for Future Development

- Always start with BeautifulSoup for HTML parsing (already in .venv)
- Use Playwright for downloading pages (handles JavaScript)
- Test in isolation with test_faculty.db before production
- Document extraction strategy before coding
- Iterate on small samples before full deployment
- Add clear section headers to extra_info for semantic search
- Use consistent field naming across all departments
- Handle missing data gracefully (don't fail entire scrape)

---

**Last Updated**: 2026-03-27
**Departments Successfully Scraped**: Physics (182), Biology (39), Mathematics (88), AMSC (175), Computer Science (174)
