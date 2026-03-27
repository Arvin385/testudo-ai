"""
Scraper for AMSC (Applied Mathematics, Statistics, and Scientific Computation) faculty.

Structure discovered:
- Single page listing: https://amsc.umd.edu/people/faculty/faculty-listing.html
- Accordion/collapsible panel structure
- Each faculty has a button div with h3 containing name/title/department
- Details are in a panel div with email, webpage, research interests
"""

from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import time
import logging
from tqdm import tqdm
import re

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

Base = declarative_base()

class CMNSFaculty(Base):
    """Faculty table matching existing structure."""
    __tablename__ = "cmns_faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    title = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    profile_url = Column(String(255))
    source_department = Column(String(255))
    bio = Column(Text)
    extra_info = Column(Text)


def parse_faculty_entry(button_div, panel_div):
    """
    Parse a single faculty entry from the accordion structure.

    Args:
        button_div: BeautifulSoup element for the button div
        panel_div: BeautifulSoup element for the panel div

    Returns:
        Dictionary with faculty information
    """
    from bs4 import BeautifulSoup

    result = {
        "name": "",
        "title": "",
        "email": "",
        "phone": "",
        "profile_url": "https://amsc.umd.edu/people/faculty/faculty-listing.html",
        "source_department": "",
        "bio": "",
        "extra_info": ""
    }

    # Parse h3 for name, title, and department
    h3 = button_div.find('h3')
    if h3:
        # Get all text nodes and spans
        h3_text = h3.get_text(' ', strip=True)

        # Find all spans with float: right which contain title and department
        right_spans = h3.find_all('span', style=lambda x: x and 'float: right' in x)

        # Extract title from first right span
        if len(right_spans) >= 1:
            result["title"] = right_spans[0].get_text().strip()

        # Extract department from second right span
        if len(right_spans) >= 2:
            result["source_department"] = right_spans[1].get_text().strip()

        # Extract name by removing title and department from full text
        name_text = h3_text
        if result["title"]:
            name_text = name_text.replace(result["title"], '')
        if result["source_department"]:
            name_text = name_text.replace(result["source_department"], '')

        # Clean up the name
        result["name"] = ' '.join(name_text.split()).strip()

    # Parse panel content for email, webpage, research
    if panel_div:
        content_div = panel_div.find('div', {'data-rlta-element': 'panel-content'})
        if content_div:
            # Get text with proper spacing
            content_html = str(content_div)
            content_text = content_div.get_text(' ', strip=True)

            # Extract email - look for the actual email address in text
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content_text)
            if email_match:
                result["email"] = email_match.group(1)

            # Extract webpage - look for URL after "Webpage:" label
            webpage_match = re.search(r'Webpage:\s*([^\s]+?)(?:\s|$)', content_text)
            if webpage_match:
                webpage = webpage_match.group(1).strip()
                # Remove trailing non-URL characters
                webpage = re.sub(r'[,\s]+$', '', webpage)
                if webpage and not webpage.lower().startswith('research'):
                    result["extra_info"] += f"WEBSITE:\n{webpage}\n\n"

            # Extract research interests - everything after "Research:"
            research_match = re.search(r'Research:\s*(.+?)(?:$)', content_text, re.DOTALL)
            if research_match:
                research = research_match.group(1).strip()
                # Clean up research text
                research = re.sub(r'\s+', ' ', research)
                result["bio"] = research

    return result


def scrape_amsc_faculty():
    """Scrape all AMSC faculty from the listing page."""

    # Setup database
    engine = create_engine("sqlite:///../tools/amsc_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching AMSC faculty listing...")
        page.goto('https://amsc.umd.edu/people/faculty/faculty-listing.html', wait_until='networkidle')
        time.sleep(2)

        # Get the HTML content
        html = page.content()

        browser.close()

    # Parse with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all button divs (accordion headers)
    button_divs = soup.find_all('div', {'role': 'button', 'data-rlta-element': 'button'})
    logging.info(f"Found {len(button_divs)} potential faculty entries")

    # Process each faculty entry
    for button_div in tqdm(button_divs, desc="AMSC Faculty"):
        # Get the h3 with name/title
        h3 = button_div.find('h3')
        if not h3:
            continue

        # Check if this is a faculty entry
        text = h3.get_text()
        if not any(title in text for title in ['Professor', 'Lecturer', 'Instructor']):
            continue

        # Get the panel ID from aria-controls
        panel_id = button_div.get('aria-controls')
        if panel_id:
            # Find the corresponding panel div
            panel_div = soup.find('div', {'id': panel_id})

            # Parse the entry
            faculty_data = parse_faculty_entry(button_div, panel_div)

            # Only add if we got a name
            if faculty_data['name']:
                all_faculty.append(faculty_data)

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} AMSC faculty members")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_amsc_faculty()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count emails and bios
    with_email = sum(1 for f in faculty if f.get('email'))
    with_webpage = sum(1 for f in faculty if 'WEBSITE' in f.get('extra_info', ''))
    with_bio = sum(1 for f in faculty if f.get('bio'))

    # Count departments
    departments = {}
    for f in faculty:
        dept = f.get('source_department', 'Unknown')
        departments[dept] = departments.get(dept, 0) + 1

    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with webpage: {with_webpage}/{len(faculty)}")
    print(f"Faculty with research interests: {with_bio}/{len(faculty)}")

    print(f"\nFaculty by department:")
    for dept, count in sorted(departments.items(), key=lambda x: -x[1])[:10]:
        print(f"  {dept}: {count}")

    print(f"\nSample entries:")
    for fac in faculty[:3]:
        print(f"\n  Name: {fac.get('name')}")
        print(f"  Title: {fac.get('title')}")
        print(f"  Department: {fac.get('source_department')}")
        print(f"  Email: {fac.get('email')}")
        bio = fac.get('bio', '')
        if bio:
            print(f"  Research: {bio[:100]}..." if len(bio) > 100 else f"  Research: {bio}")
