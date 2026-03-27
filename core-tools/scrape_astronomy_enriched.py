"""
Enhanced scraper for UMD Astronomy Department faculty with biographical information.

This scraper:
1. Filters the people page to show only Professors (value="624")
2. Collects basic info from person cards (name, title)
3. Visits each faculty profile URL to extract detailed information:
   - Biographical description
   - Research Areas
   - Research Centers & Collaborations
   - Facilities
   - Email, phone, office location
"""

from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import time
import logging
from tqdm import tqdm

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


def scrape_profile_details(page, profile_url):
    """
    Visit an Astronomy faculty profile page and extract detailed information.

    Args:
        page: Playwright page object
        profile_url: Full URL to faculty profile

    Returns:
        Dictionary with 'bio', 'extra_info', 'email', 'phone', 'title' fields
    """
    result = {
        'bio': '',
        'extra_info': '',
        'email': '',
        'phone': '',
        'title': ''
    }

    try:
        page.goto(profile_url, wait_until='networkidle', timeout=10000)
        time.sleep(1)

        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        extra_sections = []

        # 1. Extract biographical description (main research paragraph)
        bio_divs = soup.find_all('div', class_='umd-rich-text person-bio-description')
        for bio_div in bio_divs:
            # Get paragraphs (not the ones with just "Research Areas:" or similar labels)
            paragraphs = bio_div.find_all('p')
            for p in paragraphs:
                text = p.get_text(' ', strip=True)
                # If it's a substantial paragraph (not just a label), use as bio
                if len(text) > 100 and not text.startswith('Research Areas:') and not text.startswith('Research Centers'):
                    if not result['bio']:  # Only take the first substantial paragraph as bio
                        result['bio'] = text
                        break

        # 2. Extract Research Areas
        for bio_div in bio_divs:
            strong_tag = bio_div.find('strong', string=lambda x: x and 'Research Areas' in x if x else False)
            if strong_tag:
                # Get all links after this strong tag
                research_links = []
                for sibling in strong_tag.find_next_siblings():
                    if sibling.name == 'a':
                        research_links.append(sibling.get_text().strip())
                if research_links:
                    extra_sections.append("RESEARCH AREAS:\n- " + "\n- ".join(research_links))
                break

        # 3. Extract Research Centers & Collaborations
        for bio_div in bio_divs:
            strong_tag = bio_div.find('strong', string=lambda x: x and 'Research Centers' in x if x else False)
            if strong_tag:
                centers_links = []
                for sibling in strong_tag.find_next_siblings():
                    if sibling.name == 'a':
                        centers_links.append(sibling.get_text().strip())
                if centers_links:
                    extra_sections.append("RESEARCH CENTERS & COLLABORATIONS:\n- " + "\n- ".join(centers_links))
                break

        # 4. Extract Facilities
        for bio_div in bio_divs:
            strong_tag = bio_div.find('strong', string=lambda x: x and 'Facilities' in x if x else False)
            if strong_tag:
                facilities_links = []
                for sibling in strong_tag.find_next_siblings():
                    if sibling.name == 'a':
                        facilities_links.append(sibling.get_text().strip())
                if facilities_links:
                    extra_sections.append("FACILITIES:\n- " + "\n- ".join(facilities_links))
                break

        # 5. Extract contact info
        # Email
        email_link = soup.find('a', href=lambda x: x and 'mailto:' in x if x else False)
        if email_link:
            result['email'] = email_link.get('href').replace('mailto:', '')

        # Phone
        phone_link = soup.find('a', href=lambda x: x and 'tel:' in x if x else False)
        if phone_link:
            phone_field = phone_link.find('div', class_='field--name-field-ed-office-phone')
            if phone_field:
                result['phone'] = phone_field.get_text().strip()

        # Office location
        office_span = soup.find('span', class_='person-contact-item')
        if office_span:
            # Look for the one with pin icon (office location)
            svg = office_span.find('svg', id='icon_pin')
            if svg:
                office_text = office_span.get_text().strip()
                if office_text and len(office_text) > 3:
                    extra_sections.append(f"OFFICE:\n{office_text}")

        # Title
        title_p = soup.find('p', class_='person-job')
        if title_p:
            result['title'] = title_p.get_text().strip()

        # Combine all extra sections
        if extra_sections:
            result['extra_info'] = "\n\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_astronomy_enriched():
    """Scrape Astronomy faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Astronomy people page...")
        page.goto('https://www.astro.umd.edu/people', wait_until='networkidle')
        time.sleep(2)

        # Filter for Professors only
        logging.info("Filtering for Professors...")
        page.select_option('select#edit-field-astronomy-people-types-target-id', value='624')
        time.sleep(3)
        page.wait_for_load_state('networkidle')

        # Get the HTML content
        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all person blocks
        person_blocks = soup.find_all('div', class_='person-block-container')
        logging.info(f"Found {len(person_blocks)} professors")
        logging.info(f"Processing all {len(person_blocks)} entries with profile enrichment")

        # Process each faculty entry
        for block in tqdm(person_blocks, desc="Astronomy Professors"):
            entry = {
                "name": "",
                "title": "",
                "email": "",
                "phone": "",
                "profile_url": "",
                "source_department": "Astronomy",
                "bio": "",
                "extra_info": ""
            }

            # Extract name and profile URL from person block
            # Name is in: p.person-name > a
            name_p = block.find('p', class_='person-name')
            if name_p:
                name_link = name_p.find('a')
                if name_link:
                    entry['name'] = name_link.get_text().strip()
                    profile_path = name_link.get('href')
                    if profile_path:
                        if profile_path.startswith('http'):
                            entry['profile_url'] = profile_path
                        else:
                            entry['profile_url'] = f'https://www.astro.umd.edu{profile_path}'

            # Visit profile to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                entry['extra_info'] = profile_details['extra_info']
                entry['email'] = profile_details['email']
                entry['phone'] = profile_details['phone']
                entry['title'] = profile_details['title']

            # Only add if we have name and email
            if entry['name'] and entry['email']:
                all_faculty.append(entry)

        browser.close()

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"Complete! Scraped {len(all_faculty)} Astronomy faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_astronomy_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    with_email = sum(1 for f in faculty if f.get('email'))
    with_research_areas = sum(1 for f in faculty if 'RESEARCH AREAS:' in f.get('extra_info', ''))
    with_centers = sum(1 for f in faculty if 'RESEARCH CENTERS' in f.get('extra_info', ''))
    with_facilities = sum(1 for f in faculty if 'FACILITIES:' in f.get('extra_info', ''))

    print(f"Faculty with biography: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")
    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with research areas: {with_research_areas}/{len(faculty)}")
    print(f"Faculty with research centers: {with_centers}/{len(faculty)}")
    print(f"Faculty with facilities: {with_facilities}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Title: {fac.get('title')}")
            print(f"  Email: {fac.get('email')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            print(f"  Extra info preview: {fac.get('extra_info', '')[:200]}...")
            break
