"""
Enhanced scraper for UMD Geology Department faculty with biographical information.

This scraper:
1. Loads the directory table from http://www.geol.umd.edu/directory.php?view=cat
2. Extracts faculty from the "Faculty" section
3. Visits each faculty profile URL to extract detailed information:
   - Research Interests paragraphs
   - Laboratory/Website links
   - Contact information
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
    Visit a Geology faculty profile page and extract detailed information.

    Args:
        page: Playwright page object
        profile_url: Full URL to faculty profile

    Returns:
        Dictionary with 'bio' and 'extra_info' fields
    """
    result = {
        'bio': '',
        'extra_info': ''
    }

    try:
        page.goto(profile_url, wait_until='networkidle', timeout=10000)
        time.sleep(1)

        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        extra_sections = []

        # Find Research Interests section (h2 heading followed by div.section with paragraphs)
        research_heading = soup.find('h2', string=lambda x: x and 'Research Interests' in x if x else False)
        if research_heading:
            # Get the div.section after this heading
            section_div = research_heading.find_next('div', class_='section')
            if section_div:
                paragraphs = section_div.find_all('p')
                bio_parts = []
                for p in paragraphs:
                    text = p.get_text(' ', strip=True)
                    if len(text) > 50:
                        bio_parts.append(text)
                if bio_parts:
                    result['bio'] = ' '.join(bio_parts)

        # Extract Laboratory/Website links
        lab_heading = soup.find('h2', string=lambda x: x and 'Laboratory' in x if x else False)
        if lab_heading:
            section_div = lab_heading.find_next('div', class_='section')
            if section_div:
                lab_links = []
                links = section_div.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip()
                    if href and text:
                        lab_links.append(f"{text}: {href}")
                if lab_links:
                    extra_sections.append("LABORATORY/WEBSITES:\n" + "\n".join(lab_links))

        # Extract Links section (CV, Google Scholar, etc.)
        links_heading = soup.find('h2', string=lambda x: x and 'Links' in x if x else False)
        if links_heading:
            section_div = links_heading.find_next('div', class_='section')
            if section_div:
                link_items = []
                links = section_div.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip()
                    if href and text and ('CV' in text or 'Scholar' in text):
                        link_items.append(f"{text}: {href}")
                if link_items:
                    extra_sections.append("CV/LINKS:\n" + "\n".join(link_items))

        # Combine all extra sections
        if extra_sections:
            result['extra_info'] = "\n\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_geology_enriched():
    """Scrape Geology faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Geology faculty directory...")
        page.goto('http://www.geol.umd.edu/directory.php?view=cat', wait_until='networkidle')
        time.sleep(2)

        # Get the HTML content
        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find the Faculty section by anchor
        faculty_anchor = soup.find('a', id='faculty')
        if not faculty_anchor:
            logging.error("Could not find faculty section")
            browser.close()
            return []

        faculty_h2 = faculty_anchor.find_parent('h2')
        if not faculty_h2:
            logging.error("Could not find faculty h2")
            browser.close()
            return []

        # Get the table after the Faculty heading
        faculty_table = faculty_h2.find_next('table')
        if not faculty_table:
            logging.error("Could not find faculty table")
            browser.close()
            return []

        # Extract faculty from table
        rows = faculty_table.find_all('tr')[1:]  # Skip header
        logging.info(f"Found {len(rows)} faculty entries")

        faculty_list = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                name_link = cols[0].find('a')
                if name_link:
                    name = name_link.get_text().strip()
                    href = name_link.get('href')
                    title = cols[1].get_text().strip()
                    office = cols[2].get_text().strip()
                    phone = cols[3].get_text().strip()
                    email_link = cols[4].find('a')
                    email = email_link.get('href').replace('mailto:', '') if email_link else ''

                    faculty_list.append({
                        'name': name,
                        'title': title,
                        'email': email,
                        'phone': phone,
                        'profile_url': href,
                        'office': office
                    })

        logging.info(f"Processing all {len(faculty_list)} entries with profile enrichment")

        # Process each faculty entry
        for fac_data in tqdm(faculty_list, desc="Geology Faculty"):
            entry = {
                "name": fac_data['name'],
                "title": fac_data['title'],
                "email": fac_data['email'],
                "phone": fac_data['phone'],
                "profile_url": fac_data['profile_url'],
                "source_department": "Geology",
                "bio": "",
                "extra_info": ""
            }

            # Add office to extra_info
            if fac_data['office']:
                entry['extra_info'] = f"OFFICE:\n{fac_data['office']}\n\n"

            # Visit profile to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                # Append to existing extra_info
                if profile_details['extra_info']:
                    entry['extra_info'] += profile_details['extra_info']

            # Only add if we have name
            if entry['name']:
                all_faculty.append(entry)

        browser.close()

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"Complete! Scraped {len(all_faculty)} Geology faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_geology_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    with_email = sum(1 for f in faculty if f.get('email'))
    with_phone = sum(1 for f in faculty if f.get('phone'))
    with_lab = sum(1 for f in faculty if 'LABORATORY' in f.get('extra_info', ''))
    with_cv = sum(1 for f in faculty if 'CV' in f.get('extra_info', ''))

    print(f"Faculty with research interests: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")
    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with phone: {with_phone}/{len(faculty)}")
    print(f"Faculty with laboratory links: {with_lab}/{len(faculty)}")
    print(f"Faculty with CV links: {with_cv}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Title: {fac.get('title')}")
            print(f"  Email: {fac.get('email')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            print(f"  Extra info preview: {fac.get('extra_info', '')[:200]}...")
            break
