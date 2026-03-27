"""
Scraper for UMD Computer Science Department faculty.

Structure discovered:
- Directory: https://www.cs.umd.edu/people/faculty
- Profile pages: https://www.cs.umd.edu/people/{username}
- Email: Often a "Contact Form" link instead of direct mailto
- Bio: In div.field-biography
- Extra info: Research areas, education, appointments, awards, Google Scholar, etc.
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
    """Faculty table matching Clark School structure."""
    __tablename__ = "cmns_faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    title = Column(String(255))
    email = Column(String(255))  # Will contain "Contact Form" if no direct email
    phone = Column(String(50))
    profile_url = Column(String(255))
    source_department = Column(String(255))
    bio = Column(Text)
    extra_info = Column(Text)


def scrape_cs_profile(page, profile_url, faculty_name):
    """
    Visit a CS faculty profile page and extract all information.

    Args:
        page: Playwright page object
        profile_url: URL to the faculty profile
        faculty_name: Name of the faculty member

    Returns:
        Dictionary with faculty information
    """
    result = {
        "name": faculty_name,
        "profile_url": profile_url,
        "title": "",
        "email": "",
        "phone": "",
        "bio": "",
        "extra_info": ""
    }

    try:
        page.goto(profile_url, wait_until="networkidle")
        time.sleep(1)

        # Extract title
        title_h2 = page.query_selector('div.views-field-field-faculty-title h2.field-content')
        if title_h2:
            result["title"] = title_h2.inner_text().strip()

        # Extract email (might be a contact form)
        email_div = page.query_selector('div.views-field-contact')
        if email_div:
            # Check for direct mailto link
            mailto_link = email_div.query_selector('a[href^="mailto:"]')
            if mailto_link:
                result["email"] = mailto_link.get_attribute('href').replace('mailto:', '').strip()
            else:
                # Check for contact form
                contact_form = email_div.query_selector('a[href*="/contact"]')
                if contact_form:
                    result["email"] = "Contact Form: " + contact_form.get_attribute('href')

        # Extract phone
        phone_div = page.query_selector('div.views-field-field-profile-phone div.field-content')
        if phone_div:
            result["phone"] = phone_div.inner_text().strip()

        # Extract biography
        bio_div = page.query_selector('div.views-field-field-biography div.field-content')
        if bio_div:
            bio_paras = bio_div.query_selector_all('p')
            bio_parts = []
            for p in bio_paras:
                text = p.inner_text().strip()
                if text:
                    bio_parts.append(text)
            result["bio"] = " ".join(bio_parts)

        # Extract extra info (research areas, education, appointments, awards, etc.)
        extra_parts = []

        # Research areas
        research_div = page.query_selector('div.views-field-field-research-areas div.field-content')
        if research_div:
            research_text = research_div.inner_text().strip()
            if research_text:
                extra_parts.append(f"RESEARCH AREAS:\n{research_text}")

        # Education
        edu_div = page.query_selector('div.views-field-field-faculty-education div.field-content')
        if edu_div:
            edu_text = edu_div.inner_text().strip()
            if edu_text:
                extra_parts.append(f"EDUCATION:\n{edu_text}")

        # Appointments
        appt_div = page.query_selector('div.views-field-field-faculty-appointment-1 div.field-content')
        if appt_div:
            appt_text = appt_div.inner_text().strip()
            if appt_text:
                extra_parts.append(f"APPOINTMENTS:\n{appt_text}")

        # Location/Office
        location_div = page.query_selector('div.views-field-field-profile-location div.field-content')
        if location_div:
            location_text = location_div.inner_text().strip()
            if location_text:
                extra_parts.append(f"OFFICE:\n{location_text}")

        # Website
        website_div = page.query_selector('div.views-field-field-profile-website div.field-content a')
        if website_div:
            website = website_div.get_attribute('href')
            if website:
                extra_parts.append(f"WEBSITE:\n{website}")

        # Google Scholar
        gscholar_div = page.query_selector('div.views-field-field-profile-gscholar div.field-content a')
        if gscholar_div:
            gscholar = gscholar_div.get_attribute('href')
            if gscholar:
                extra_parts.append(f"GOOGLE SCHOLAR:\n{gscholar}")

        # Honors and Awards
        awards_table = page.query_selector('table.views-table')
        if awards_table:
            awards_rows = awards_table.query_selector_all('tbody tr')
            if awards_rows:
                awards_list = []
                for row in awards_rows:
                    year = row.query_selector('td.views-field-field-award-year')
                    award_type = row.query_selector('td.views-field-field-award-type')
                    org = row.query_selector('td.views-field-field-award-organization')
                    title = row.query_selector('td.views-field-title strong')

                    if title:
                        award_text = title.inner_text().strip()
                        if year:
                            award_text = f"{year.inner_text().strip()}: {award_text}"
                        if org:
                            org_text = org.inner_text().strip()
                            if org_text:
                                award_text += f" ({org_text})"
                        awards_list.append(award_text)

                if awards_list:
                    extra_parts.append(f"HONORS AND AWARDS:\n" + "\n".join(f"- {a}" for a in awards_list))

        result["extra_info"] = "\n\n".join(extra_parts)

    except Exception as e:
        logging.error(f"Error scraping profile {profile_url}: {e}")

    return result


def scrape_cs_faculty():
    """Scrape all CS department faculty."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching CS faculty directory...")
        page.goto('https://www.cs.umd.edu/people/faculty', wait_until='networkidle')
        time.sleep(2)

        # Extract all faculty profile links
        faculty_cards = page.query_selector_all('div.media.col-xs-12 h4.media-heading a')
        logging.info(f"Found {len(faculty_cards)} faculty members")

        faculty_urls = []
        for card in faculty_cards:
            href = card.get_attribute('href')
            name = card.inner_text().strip()
            full_url = f'https://www.cs.umd.edu{href}'
            faculty_urls.append({'name': name, 'url': full_url})

        # Scrape each faculty profile
        logging.info(f"\nScraping {len(faculty_urls)} faculty profiles...")
        for faculty_info in tqdm(faculty_urls, desc="CS Faculty"):
            profile_data = scrape_cs_profile(page, faculty_info['url'], faculty_info['name'])
            profile_data['source_department'] = "Computer Science"
            all_faculty.append(profile_data)
            time.sleep(0.5)  # Be polite to the server

        browser.close()

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} CS faculty members")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_cs_faculty()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count emails and bios
    with_direct_email = sum(1 for f in faculty if f.get('email') and not f['email'].startswith('Contact Form'))
    with_contact_form = sum(1 for f in faculty if f.get('email') and f['email'].startswith('Contact Form'))
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))

    print(f"Faculty with direct email: {with_direct_email}/{len(faculty)}")
    print(f"Faculty with contact form: {with_contact_form}/{len(faculty)}")
    print(f"Faculty with bios: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")

    print(f"\nSample entries:")
    for fac in faculty[:3]:
        print(f"\n  Name: {fac.get('name')}")
        print(f"  Title: {fac.get('title')}")
        print(f"  Email: {fac.get('email')}")
        print(f"  Phone: {fac.get('phone')}")
        bio = fac.get('bio', '')
        if bio:
            print(f"  Bio: {bio[:150]}..." if len(bio) > 150 else f"  Bio: {bio}")
        extra = fac.get('extra_info', '')
        if extra:
            print(f"  Extra info length: {len(extra)} chars")
