"""
Test script for Smith School scraper - processes only first 10 faculty.
"""

from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import time
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

Base = declarative_base()

class TestFaculty(Base):
    """Test faculty table."""
    __tablename__ = "test_faculty"
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
    """Visit a Smith School faculty profile and extract detailed information."""
    result = {
        'bio': '',
        'title': '',
        'email': '',
        'phone': '',
        'extra_info': ''
    }

    try:
        page.goto(profile_url, wait_until='networkidle', timeout=10000)
        time.sleep(1)

        html = page.content()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract biographical content
        bio_div = soup.find('div', class_='profile-bio')
        if bio_div:
            paragraphs = bio_div.find_all('p')
            bio_parts = []
            for p in paragraphs:
                text = p.get_text(' ', strip=True)
                if len(text) > 50:
                    bio_parts.append(text)
            if bio_parts:
                result['bio'] = ' '.join(bio_parts)

        # Extract title
        title_divs = soup.find_all('div', class_='profile-title')
        titles = []
        for div in title_divs:
            p_tag = div.find('p')
            if p_tag:
                text = p_tag.get_text().strip()
                if text and 'Ph.D.' not in text and 'M.A.' not in text and 'B.A.' not in text:
                    titles.append(text)
        if titles:
            result['title'] = titles[0]

        # Extract email
        email_link = soup.find('a', href=lambda x: x and 'mailto:' in x if x else False)
        if email_link:
            result['email'] = email_link.get('href').replace('mailto:', '')

        # Extract phone
        phone_div = soup.find('div', class_='profile-phone')
        if phone_div:
            phone_link = phone_div.find('a')
            if phone_link:
                result['phone'] = phone_link.get_text().strip()

        # Extract office and website
        extra_sections = []

        contact_divs = soup.find_all('div', class_='col-600-12 col-1000-3 editor-content')
        for contact_div in contact_divs:
            for div in contact_div.find_all('div', recursive=False):
                text = div.get_text().strip()
                if text and ('Hall' in text or 'Room' in text or 'Building' in text):
                    extra_sections.append(f"OFFICE:\n{text}")
                    break

        website_link = soup.find('a', string='Personal Website')
        if website_link:
            href = website_link.get('href')
            if href:
                extra_sections.append(f"PERSONAL WEBSITE:\n{href}")

        if extra_sections:
            result['extra_info'] = '\n\n'.join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")

    return result


def test_smith_scraper():
    """Test Smith scraper on first 10 faculty."""

    # Setup test database
    engine = create_engine("sqlite:///test_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Smith School directory (first page only)...")
        page.goto('https://www.rhsmith.umd.edu/directory', wait_until='networkidle')
        time.sleep(2)

        html = page.content()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find first 10 profiles
        person_divs = soup.find_all('div', class_='col-12 mb-4')[:10]

        profile_links = []
        for person_div in person_divs:
            name_p = person_div.find('p', class_='person-name')
            if name_p:
                name_link = name_p.find('a')
                if name_link:
                    name = name_link.get_text().strip()
                    href = name_link.get('href')
                    if href:
                        if href.startswith('http'):
                            profile_url = href
                        else:
                            profile_url = f'https://www.rhsmith.umd.edu{href}'
                        profile_links.append((name, profile_url))

        logging.info(f"Testing with {len(profile_links)} faculty profiles")

        # Process each faculty entry
        for name, profile_url in tqdm(profile_links, desc="Smith Faculty (Test)"):
            entry = {
                "name": name,
                "title": "",
                "email": "",
                "phone": "",
                "profile_url": profile_url,
                "source_department": "Robert H. Smith School of Business",
                "bio": "",
                "extra_info": ""
            }

            profile_details = scrape_profile_details(page, entry['profile_url'])
            entry['bio'] = profile_details['bio']
            entry['title'] = profile_details['title']
            entry['email'] = profile_details['email']
            entry['phone'] = profile_details['phone']
            entry['extra_info'] = profile_details['extra_info']

            if entry['name'] and entry['email']:
                all_faculty.append(entry)

        browser.close()

    # Save to test database
    logging.info(f"\nSaving {len(all_faculty)} faculty to test database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(TestFaculty(**fac))

    session.commit()
    session.close()

    # Print results
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Total faculty scraped: {len(all_faculty)}")

    with_bio = sum(1 for f in all_faculty if f.get('bio'))
    with_email = sum(1 for f in all_faculty if f.get('email'))
    with_phone = sum(1 for f in all_faculty if f.get('phone'))
    with_title = sum(1 for f in all_faculty if f.get('title'))
    with_office = sum(1 for f in all_faculty if 'OFFICE' in f.get('extra_info', ''))
    with_website = sum(1 for f in all_faculty if 'WEBSITE' in f.get('extra_info', ''))

    print(f"Faculty with biography: {with_bio}/{len(all_faculty)} ({100*with_bio//len(all_faculty) if all_faculty else 0}%)")
    print(f"Faculty with email: {with_email}/{len(all_faculty)}")
    print(f"Faculty with phone: {with_phone}/{len(all_faculty)}")
    print(f"Faculty with title: {with_title}/{len(all_faculty)}")
    print(f"Faculty with office: {with_office}/{len(all_faculty)}")
    print(f"Faculty with personal website: {with_website}/{len(all_faculty)}")

    print(f"\n" + "-"*60)
    print("SAMPLE ENTRIES:")
    print("-"*60)
    for i, fac in enumerate(all_faculty[:3], 1):
        print(f"\n{i}. {fac.get('name')}")
        print(f"   Title: {fac.get('title')}")
        print(f"   Email: {fac.get('email')}")
        print(f"   Phone: {fac.get('phone')}")
        print(f"   Bio: {fac.get('bio')[:150]}..." if fac.get('bio') else "   Bio: (none)")
        print(f"   Extra: {fac.get('extra_info')[:100]}..." if fac.get('extra_info') else "   Extra: (none)")

    return all_faculty


if __name__ == "__main__":
    test_smith_scraper()
