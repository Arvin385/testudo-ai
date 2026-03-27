"""
Enhanced scraper for UMD Atmospheric & Oceanic Science Department faculty with biographical information.

This scraper:
1. Loads the main people page (https://aosc.umd.edu/people)
2. Extracts profile links for all faculty
3. Visits each faculty profile URL to extract detailed information:
   - Research interests paragraph
   - Email address
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
    Visit an AOSC faculty profile page and extract detailed information.

    Args:
        page: Playwright page object
        profile_url: Full URL to faculty profile

    Returns:
        Dictionary with 'bio', 'email', 'title' fields
    """
    result = {
        'bio': '',
        'email': '',
        'title': ''
    }

    try:
        page.goto(profile_url, wait_until='networkidle', timeout=10000)
        time.sleep(1)

        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract research interests - look for substantial paragraphs
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(' ', strip=True)
            # Look for paragraphs that mention research or are substantial
            if len(text) > 100 and ('research' in text.lower() or 'interests' in text.lower() or 'focus' in text.lower()):
                if not result['bio']:  # Only take the first one
                    result['bio'] = text
                    break

        # If didn't find research-specific, take any substantial paragraph
        if not result['bio']:
            for p in paragraphs:
                text = p.get_text(' ', strip=True)
                if len(text) > 150:
                    result['bio'] = text
                    break

        # Extract email
        email_link = soup.find('a', href=lambda x: x and 'mailto:' in x if x else False)
        if email_link:
            result['email'] = email_link.get('href').replace('mailto:', '')

        # Extract title (may be in h2 or other locations)
        # Look for title-like text
        title_candidates = soup.find_all(['h2', 'h3', 'p'])
        for elem in title_candidates:
            text = elem.get_text().strip()
            if any(keyword in text.lower() for keyword in ['professor', 'lecturer', 'scientist', 'director']):
                if len(text) < 100:  # Not a full paragraph
                    result['title'] = text
                    break

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_aosc_enriched():
    """Scrape AOSC faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching AOSC people page...")
        page.goto('https://aosc.umd.edu/people', wait_until='networkidle')
        time.sleep(3)

        # Get the HTML content
        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all profile links
        profile_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            # Profile links have /people/ and hyphenated names
            if href and '/people/' in href and '-' in href and len(text) > 5:
                # Filter out single-letter navigation links
                if not (len(href.split('/')[-1]) == 1):
                    # Convert to absolute URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f'https://aosc.umd.edu{href}'
                    profile_links.append((text, full_url))

        # Remove duplicates
        seen = set()
        unique_profiles = []
        for text, url in profile_links:
            if url not in seen:
                seen.add(url)
                unique_profiles.append((text, url))

        logging.info(f"Found {len(unique_profiles)} faculty profiles")
        logging.info(f"Processing all {len(unique_profiles)} entries with profile enrichment")

        # Process each faculty entry
        for name, profile_url in tqdm(unique_profiles, desc="AOSC Faculty"):
            entry = {
                "name": name,
                "title": "",
                "email": "",
                "phone": "",
                "profile_url": profile_url,
                "source_department": "Atmospheric & Oceanic Science",
                "bio": "",
                "extra_info": ""
            }

            # Visit profile to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                entry['email'] = profile_details['email']
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

    logging.info(f"Complete! Scraped {len(all_faculty)} AOSC faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_aosc_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_email = sum(1 for f in faculty if f.get('email'))
    with_title = sum(1 for f in faculty if f.get('title'))

    print(f"Faculty with research interests: {with_bio}/{len(faculty)}")
    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with title: {with_title}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Title: {fac.get('title')}")
            print(f"  Email: {fac.get('email')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            break
