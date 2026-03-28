"""
Enhanced scraper for UMD Robert H. Smith School of Business faculty with biographical information.

This scraper:
1. Loads the directory page (https://www.rhsmith.umd.edu/directory)
2. Navigates through all paginated pages to collect faculty profile links
3. Visits each faculty profile URL to extract detailed information:
   - Biographical paragraphs
   - Title and position
   - Contact information (email, phone, office)
   - Personal website links
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
    Visit a Smith School faculty profile page and extract detailed information.

    Args:
        page: Playwright page object
        profile_url: Full URL to faculty profile

    Returns:
        Dictionary with 'bio', 'title', 'email', 'phone', 'extra_info' fields
    """
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

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract biographical content from profile-bio div
        bio_div = soup.find('div', class_='profile-bio')
        if bio_div:
            paragraphs = bio_div.find_all('p')
            bio_parts = []
            for p in paragraphs:
                text = p.get_text(' ', strip=True)
                if len(text) > 50:  # Only substantial paragraphs
                    bio_parts.append(text)
            if bio_parts:
                result['bio'] = ' '.join(bio_parts)

        # Extract title from profile-title divs
        title_divs = soup.find_all('div', class_='profile-title')
        titles = []
        for div in title_divs:
            p_tag = div.find('p')
            if p_tag:
                text = p_tag.get_text().strip()
                if text and 'Ph.D.' not in text and 'M.A.' not in text and 'B.A.' not in text:
                    titles.append(text)
        if titles:
            result['title'] = titles[0]  # Take the first title

        # Extract email
        email_link = soup.find('a', href=lambda x: x and 'mailto:' in x if x else False)
        if email_link:
            result['email'] = email_link.get('href').replace('mailto:', '')

        # Extract phone from profile-phone div
        phone_div = soup.find('div', class_='profile-phone')
        if phone_div:
            phone_link = phone_div.find('a')
            if phone_link:
                result['phone'] = phone_link.get_text().strip()

        # Extract office location and personal website for extra_info
        extra_sections = []

        # Office location - look for divs in the contact section that contain office info
        # It's in the same column as email/phone but is plain text
        contact_divs = soup.find_all('div', class_='col-600-12 col-1000-3 editor-content')
        for contact_div in contact_divs:
            # Find all divs, look for ones that look like office locations
            for div in contact_div.find_all('div', recursive=False):
                text = div.get_text().strip()
                # Office locations typically contain "Hall" or "Room"
                if text and ('Hall' in text or 'Room' in text or 'Building' in text):
                    extra_sections.append(f"OFFICE:\n{text}")
                    break

        # Personal website
        website_link = soup.find('a', string='Personal Website')
        if website_link:
            href = website_link.get('href')
            if href:
                extra_sections.append(f"PERSONAL WEBSITE:\n{href}")

        # Combine extra sections
        if extra_sections:
            result['extra_info'] = '\n\n'.join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_smith_enriched():
    """Scrape Smith School faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Smith School directory page...")
        page.goto('https://www.rhsmith.umd.edu/directory', wait_until='networkidle')
        time.sleep(2)

        # Collect all profile URLs by paginating through directory
        profile_links = []
        page_num = 1

        while True:
            logging.info(f"Collecting profiles from page {page_num}...")

            html = page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')

            # Find all profile cards
            person_divs = soup.find_all('div', class_='col-12 mb-4')

            for person_div in person_divs:
                # Name is in p.h3.person-name > a
                name_p = person_div.find('p', class_='person-name')
                if name_p:
                    name_link = name_p.find('a')
                    if name_link:
                        name = name_link.get_text().strip()
                        href = name_link.get('href')
                        if href:
                            # Convert to absolute URL
                            if href.startswith('http'):
                                profile_url = href
                            else:
                                profile_url = f'https://www.rhsmith.umd.edu{href}'
                            profile_links.append((name, profile_url))

            # Try to find and click "Next" button
            # Look for pagination - typically a "next" link or button
            next_button = None
            try:
                # Try to find next page link
                next_link = page.locator('a:has-text("Next")').first
                if next_link.is_visible():
                    next_button = next_link
            except:
                pass

            if next_button:
                try:
                    next_button.click()
                    page.wait_for_load_state('networkidle')
                    time.sleep(2)
                    page_num += 1
                except:
                    # No more pages
                    break
            else:
                # No next button found, we're done
                break

        # Remove duplicates
        seen = set()
        unique_profiles = []
        for name, url in profile_links:
            if url not in seen:
                seen.add(url)
                unique_profiles.append((name, url))

        logging.info(f"Found {len(unique_profiles)} unique faculty profiles")
        logging.info(f"Processing all {len(unique_profiles)} entries with profile enrichment")

        # Process each faculty entry
        for name, profile_url in tqdm(unique_profiles, desc="Smith Faculty"):
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

            # Visit profile to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                entry['title'] = profile_details['title']
                entry['email'] = profile_details['email']
                entry['phone'] = profile_details['phone']
                entry['extra_info'] = profile_details['extra_info']

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

    logging.info(f"Complete! Scraped {len(all_faculty)} Smith faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_smith_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_email = sum(1 for f in faculty if f.get('email'))
    with_phone = sum(1 for f in faculty if f.get('phone'))
    with_title = sum(1 for f in faculty if f.get('title'))
    with_office = sum(1 for f in faculty if 'OFFICE' in f.get('extra_info', ''))
    with_website = sum(1 for f in faculty if 'WEBSITE' in f.get('extra_info', ''))

    print(f"Faculty with biography: {with_bio}/{len(faculty)} ({100*with_bio//len(faculty) if faculty else 0}%)")
    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with phone: {with_phone}/{len(faculty)}")
    print(f"Faculty with title: {with_title}/{len(faculty)}")
    print(f"Faculty with office: {with_office}/{len(faculty)}")
    print(f"Faculty with personal website: {with_website}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Title: {fac.get('title')}")
            print(f"  Email: {fac.get('email')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            if fac.get('extra_info'):
                print(f"  Extra info preview: {fac.get('extra_info')[:100]}...")
            break
