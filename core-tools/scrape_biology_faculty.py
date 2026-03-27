"""
Scraper for UMD Biology Department faculty.

Structure discovered:
- Page: https://biology.umd.edu/people
- Faculty info in div.team-name elements
- Contains: name, title, email, profile URL
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


def scrape_biology_faculty():
    """Scrape all Biology department faculty from the listing page."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Biology faculty listing...")
        page.goto('https://biology.umd.edu/people', wait_until='networkidle')
        time.sleep(3)

        # Get the HTML content
        html = page.content()

        browser.close()

    # Parse with BeautifulSoup
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all team-name divs (each represents one faculty member)
    name_divs = soup.find_all('div', class_='team-name')
    logging.info(f"Found {len(name_divs)} potential faculty entries")

    # Process each faculty entry
    for name_div in tqdm(name_divs, desc="Biology Faculty"):
        entry = {
            "name": "",
            "title": "",
            "email": "",
            "phone": "",
            "profile_url": "",
            "source_department": "Biology",
            "bio": "",
            "extra_info": ""
        }

        # Extract name
        name_link = name_div.find('a')
        if name_link:
            entry['name'] = name_link.get_text().strip()
            profile_path = name_link.get('href')
            # Build full URL
            if profile_path:
                if profile_path.startswith('http'):
                    entry['profile_url'] = profile_path
                else:
                    entry['profile_url'] = f'https://biology.umd.edu{profile_path}'

        # Find the parent container that has all the info
        parent = name_div.find_parent('div', class_=lambda x: x and 'views-row' in str(x) if x else False)

        if not parent:
            # Try broader search
            parent = name_div.find_parent('div')
            for _ in range(5):
                if parent and len(list(parent.find_all('div', recursive=False))) > 3:
                    break
                parent = parent.find_parent('div') if parent else None

        if parent:
            # Extract title
            title_div = parent.find('div', class_='field--name-field-team-position')
            if title_div:
                entry['title'] = title_div.get_text().strip()

            # Extract email
            email_link = parent.find('a', href=lambda x: x and 'mailto:' in x if x else False)
            if email_link:
                entry['email'] = email_link.get('href').replace('mailto:', '')

        # Only add if we have name and email
        if entry['name'] and entry['email']:
            all_faculty.append(entry)

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} Biology faculty members")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_biology_faculty()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count fields
    with_email = sum(1 for f in faculty if f.get('email'))
    with_title = sum(1 for f in faculty if f.get('title'))
    with_profile = sum(1 for f in faculty if f.get('profile_url'))

    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with title: {with_title}/{len(faculty)}")
    print(f"Faculty with profile URL: {with_profile}/{len(faculty)}")

    # Count by title type
    titles = {}
    for f in faculty:
        title = f.get('title', 'Unknown')
        titles[title] = titles.get(title, 0) + 1

    print(f"\nFaculty by title:")
    for title, count in sorted(titles.items(), key=lambda x: -x[1])[:10]:
        print(f"  {title}: {count}")

    print(f"\nSample entries:")
    for fac in faculty[:3]:
        print(f"\n  Name: {fac.get('name')}")
        print(f"  Title: {fac.get('title')}")
        print(f"  Email: {fac.get('email')}")
