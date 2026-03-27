"""
Scraper for UMD Mathematics Department faculty.

Structure discovered:
- Single page listing: https://www-math.umd.edu/people/faculty.html
- Faculty info in div.catItemExtraFields elements
- Contains: name, title, email, office, phone, personal website, profile URL
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


def scrape_physics_faculty():
    """Scrape all Mathematics department faculty from the listing page."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Mathematics faculty listing...")
        page.goto('https://www-math.umd.edu/people/faculty.html', wait_until='networkidle')
        time.sleep(3)

        # Get the HTML content
        html = page.content()

        browser.close()

    # Parse with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all faculty entries
    extra_fields_divs = soup.find_all('div', class_='catItemExtraFields')
    logging.info(f"Found {len(extra_fields_divs)} potential faculty entries")

    # Process each faculty entry
    for div in tqdm(extra_fields_divs, desc="Mathematics Faculty"):
        entry = {
            "name": "",
            "title": "",
            "email": "",
            "phone": "",
            "profile_url": "",
            "source_department": "Mathematics",
            "bio": "",
            "extra_info": ""
        }

        # Get the parent item container
        item_container = div.find_parent('div', class_=lambda x: x and 'catItem' in str(x) if x else False)

        if item_container:
            # Look for name in heading
            name_elem = item_container.find(['h2', 'h3', 'h4'], class_=lambda x: x and 'catItemTitle' in str(x) if x else False)
            if name_elem:
                name_link = name_elem.find('a')
                entry['name'] = name_link.get_text().strip() if name_link else name_elem.get_text().strip()

        # Extract info from the div text
        div_text = div.get_text('\n').strip()

        # Email
        email_link = div.find('a', href=lambda x: x and 'mailto:' in x if x else False)
        if email_link:
            entry['email'] = email_link.get('href').replace('mailto:', '')

        # Title
        title_match = re.search(r'Title\s+(.+?)(?:\n|E-mail|Address|Phone|Web Page|$)', div_text)
        if title_match:
            entry['title'] = title_match.group(1).strip()

        # Address/Office
        address_match = re.search(r'Address\s+(.+?)(?:\n|Phone|Web Page|$)', div_text)
        if address_match:
            office = address_match.group(1).strip()
            entry['extra_info'] += f"OFFICE:\n{office}\n\n"

        # Phone
        phone_match = re.search(r'Phone\s+(.+?)(?:\n|Web Page|$)', div_text)
        if phone_match:
            entry['phone'] = phone_match.group(1).strip()

        # Personal website and profile URL
        web_links = div.find_all('a', href=True)
        for link in web_links:
            link_text = link.get_text().strip()
            href = link.get('href')

            if 'Personal Website' in link_text:
                personal_website = href if href.startswith('http') else f'https://www-math.umd.edu{href}'
                entry['extra_info'] += f"WEBSITE:\n{personal_website}\n\n"

            elif 'Department Profile' in link_text:
                # Make sure it's a full URL
                if href.startswith('http'):
                    entry['profile_url'] = href
                else:
                    entry['profile_url'] = f'https://www-math.umd.edu{href}'

        # Only add if we have name and email
        if entry['name'] and entry['email']:
            all_faculty.append(entry)

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} Mathematics faculty members")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_physics_faculty()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count emails, phones, websites
    with_email = sum(1 for f in faculty if f.get('email'))
    with_phone = sum(1 for f in faculty if f.get('phone'))
    with_website = sum(1 for f in faculty if 'WEBSITE' in f.get('extra_info', ''))
    with_office = sum(1 for f in faculty if 'OFFICE' in f.get('extra_info', ''))

    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with phone: {with_phone}/{len(faculty)}")
    print(f"Faculty with personal website: {with_website}/{len(faculty)}")
    print(f"Faculty with office location: {with_office}/{len(faculty)}")

    # Count by title type
    titles = {}
    for f in faculty:
        title = f.get('title', 'Unknown')
        # Simplify titles
        if 'Professor' in title:
            if 'Emeritus' in title:
                category = 'Emeritus'
            elif 'Affiliate' in title:
                category = 'Affiliate'
            elif 'Adjunct' in title:
                category = 'Adjunct'
            elif 'Research' in title:
                category = 'Research'
            elif 'Assistant' in title:
                category = 'Assistant Professor'
            elif 'Associate' in title:
                category = 'Associate Professor'
            else:
                category = 'Professor'
        else:
            category = title
        titles[category] = titles.get(category, 0) + 1

    print(f"\nFaculty by category:")
    for title, count in sorted(titles.items(), key=lambda x: -x[1])[:10]:
        print(f"  {title}: {count}")

    print(f"\nSample entries:")
    for fac in faculty[:3]:
        print(f"\n  Name: {fac.get('name')}")
        print(f"  Title: {fac.get('title')}")
        print(f"  Email: {fac.get('email')}")
        print(f"  Phone: {fac.get('phone')}")
