"""
Enhanced scraper for UMD Biology Department faculty with biographical information.

This scraper:
1. Collects basic info from main faculty listing (name, email, title)
2. Visits each faculty profile URL to extract detailed information:
   - Research interests/description
   - Graduate program affiliations
   - Awards
   - Education
   - Publications (Google Scholar/PubMed links)
   - Lab/personal website
   - Additional titles
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
    Visit a Biology faculty profile page and extract detailed information.

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

        # 1. Main body field - contains research interests, affiliations, awards, education, publications
        # Note: There are multiple field--name-body divs, we need the one with actual content (has headings)
        body_fields = soup.find_all('div', class_='field--name-body')
        content_div = None
        for body_field in body_fields:
            # Check if this div has headings (indicates it's the content div)
            if body_field.find(['h2', 'h3', 'h4']):
                content_div = body_field
                break

        if content_div:
            # Extract sections separately

            # Research Interests (main bio)
            research_heading = content_div.find(['h2', 'h3', 'h4'], string=lambda x: x and 'research interest' in x.lower() if x else False)
            if research_heading:
                # Get the paragraph after this heading
                research_p = research_heading.find_next('p')
                if research_p:
                    result['bio'] = research_p.get_text(' ', strip=True)

            # Graduate Program Affiliations
            affiliation_heading = content_div.find(['h2', 'h3', 'h4'], string=lambda x: x and 'graduate program' in x.lower() if x else False)
            if affiliation_heading:
                # Get the ul after this heading
                affil_list = affiliation_heading.find_next('ul')
                if affil_list:
                    items = affil_list.find_all('li')
                    affiliations = [item.get_text(' ', strip=True) for item in items]
                    if affiliations:
                        extra_sections.append("GRADUATE PROGRAM AFFILIATIONS:\\n- " + "\\n- ".join(affiliations))

            # Awards
            awards_heading = content_div.find(['h2', 'h3', 'h4'], string=lambda x: x and 'award' in x.lower() if x else False)
            if awards_heading:
                awards_list = awards_heading.find_next('ul')
                if awards_list:
                    items = awards_list.find_all('li')
                    awards = [item.get_text(' ', strip=True) for item in items]
                    if awards:
                        extra_sections.append("AWARDS:\\n- " + "\\n- ".join(awards))

            # Education
            edu_heading = content_div.find(['h2', 'h3', 'h4'], string=lambda x: x and 'education' in x.lower() if x else False)
            if edu_heading:
                edu_list = edu_heading.find_next('ul')
                if edu_list:
                    items = edu_list.find_all('li')
                    education = [item.get_text(' ', strip=True) for item in items]
                    if education:
                        extra_sections.append("EDUCATION:\\n- " + "\\n- ".join(education))

            # Publications links (Google Scholar, PubMed)
            pub_heading = content_div.find(['h2', 'h3', 'h4'], string=lambda x: x and 'publication' in x.lower() if x else False)
            if pub_heading:
                # Get links after this heading
                pub_links = []
                for sibling in pub_heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        break
                    links = sibling.find_all('a', href=True)
                    for link in links:
                        href = link.get('href')
                        if 'scholar.google' in href or 'pubmed' in href:
                            pub_links.append(href)
                if pub_links:
                    extra_sections.append("PUBLICATIONS:\\n" + "\\n".join(pub_links))

        # 2. Lab/Personal Website
        website_field = soup.find('div', class_='field--name-field-team-website')
        if website_field:
            link = website_field.find('a', href=True)
            if link:
                website_url = link.get('href')
                website_text = link.get_text().strip()
                extra_sections.append(f"LAB/PERSONAL WEBSITE:\\n{website_text}: {website_url}")

        # 3. Additional Titles
        titles_field = soup.find('div', class_='field--name-field-team-additional-titles')
        if titles_field:
            content = titles_field.find('div', class_='field__item')
            if content:
                titles = content.get_text(' ', strip=True)
                if titles:
                    extra_sections.append(f"ADDITIONAL TITLES:\\n{titles}")

        # 4. Contact Information (office phone, lab phone, office address)
        contact_field = soup.find('div', class_='field--name-field-team-contact')
        if contact_field:
            contact_text = contact_field.get_text(' ', strip=True)
            if contact_text:
                extra_sections.append(f"CONTACT:\\n{contact_text}")

        # Combine all extra sections
        if extra_sections:
            result['extra_info'] = "\\n\\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_biology_enriched():
    """Scrape Biology faculty with enriched biographical information."""

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

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all team-name divs (each represents one faculty member)
        name_divs = soup.find_all('div', class_='team-name')
        logging.info(f"Found {len(name_divs)} potential faculty entries")
        logging.info(f"Processing all {len(name_divs)} entries with profile enrichment")

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

            # Extract name and profile URL
            name_link = name_div.find('a')
            if name_link:
                entry['name'] = name_link.get_text().strip()
                profile_path = name_link.get('href')
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

            # If we have a profile URL, visit it to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                entry['extra_info'] = profile_details['extra_info']

            # Only add if we have name and email
            if entry['name'] and entry['email']:
                all_faculty.append(entry)

        browser.close()

    # Save to database
    logging.info(f"\\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(CMNSFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} Biology faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_biology_enriched()

    # Print summary
    print("\\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    with_affiliations = sum(1 for f in faculty if 'GRADUATE PROGRAM' in f.get('extra_info', ''))
    with_awards = sum(1 for f in faculty if 'AWARDS:' in f.get('extra_info', ''))
    with_education = sum(1 for f in faculty if 'EDUCATION:' in f.get('extra_info', ''))
    with_publications = sum(1 for f in faculty if 'PUBLICATIONS:' in f.get('extra_info', ''))
    with_website = sum(1 for f in faculty if 'WEBSITE:' in f.get('extra_info', ''))

    print(f"Faculty with research interests: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")
    print(f"Faculty with graduate affiliations: {with_affiliations}/{len(faculty)}")
    print(f"Faculty with awards: {with_awards}/{len(faculty)}")
    print(f"Faculty with education: {with_education}/{len(faculty)}")
    print(f"Faculty with publication links: {with_publications}/{len(faculty)}")
    print(f"Faculty with lab website: {with_website}/{len(faculty)}")

    print(f"\\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\\n  Name: {fac.get('name')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            print(f"  Extra info preview: {fac.get('extra_info', '')[:200]}...")
            break
