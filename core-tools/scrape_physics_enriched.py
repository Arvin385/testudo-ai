"""
Enhanced scraper for UMD Physics Department faculty with biographical information.

This scraper:
1. Collects basic info from main faculty listing (name, email, title, phone, office)
2. Visits each faculty profile URL to extract detailed information:
   - Biography (div#biography)
   - CV link
   - Personal website (already captured)
   - Research areas and publications (div#research)
   - Teaching courses (div#teaching)
   - News items (div#news)
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


def scrape_profile_details(page, profile_url):
    """
    Visit a faculty profile page and extract detailed biographical information.

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

        # 1. Curriculum Vitae link
        cv_link = soup.find('a', href=lambda x: x and '/images/CV/' in x if x else False)
        if cv_link:
            cv_url = cv_link.get('href')
            if not cv_url.startswith('http'):
                cv_url = f'https://umdphysics.umd.edu{cv_url}'
            extra_sections.append(f"CURRICULUM VITAE:\n{cv_url}")

        # 2. Personal Website (if not already captured)
        website_link = soup.find('a', string='Personal Website')
        if website_link:
            website_url = website_link.get('href')
            extra_sections.append(f"PERSONAL WEBSITE:\n{website_url}")

        # 3. Biography tab
        bio_tab = soup.find('div', id='biography')
        if bio_tab:
            # Remove the heading text
            bio_text = bio_tab.get_text(' ', strip=True)
            bio_text = bio_text.replace('Biography', '', 1).strip()
            if bio_text:
                result['bio'] = bio_text

        # 4. Research tab
        research_tab = soup.find('div', id='research')
        if research_tab:
            research_content = []

            # Research areas
            research_areas = research_tab.find_all('a', href=lambda x: x and 'research-areas' in x if x else False)
            if research_areas:
                areas_list = [area.get_text().strip() for area in research_areas]
                research_content.append("Research Areas:\n- " + "\n- ".join(areas_list))

            # Publications
            pubs = research_tab.find_all('li')
            if pubs:
                pub_list = []
                for pub in pubs:
                    pub_text = pub.get_text(' ', strip=True)
                    if len(pub_text) > 20:  # Filter out empty or very short items
                        pub_list.append(pub_text)
                if pub_list:
                    research_content.append("Notable Publications:\n- " + "\n- ".join(pub_list))

            if research_content:
                extra_sections.append("RESEARCH:\n" + "\n\n".join(research_content))

        # 5. Teaching tab
        teaching_tab = soup.find('div', id='teaching')
        if teaching_tab:
            courses = teaching_tab.find_all('a')
            if courses:
                course_list = [course.get_text().strip() for course in courses if course.get_text().strip()]
                if course_list:
                    extra_sections.append("TEACHING:\n- " + "\n- ".join(course_list))

        # 6. News tab
        news_tab = soup.find('div', id='news')
        if news_tab:
            news_items = news_tab.find_all('a')
            if news_items:
                news_list = [item.get_text().strip() for item in news_items if item.get_text().strip()]
                if news_list:
                    extra_sections.append("NEWS:\n- " + "\n- ".join(news_list))

        # Combine all extra sections
        if extra_sections:
            result['extra_info'] = "\n\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_physics_enriched():
    """Scrape Physics faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Physics faculty listing...")
        page.goto('https://umdphysics.umd.edu/people/faculty.html', wait_until='networkidle')
        time.sleep(3)

        # Get the HTML content
        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all faculty entries
        extra_fields_divs = soup.find_all('div', class_='catItemExtraFields')
        logging.info(f"Found {len(extra_fields_divs)} potential faculty entries")

        # Full scrape of all faculty
        logging.info(f"Processing all {len(extra_fields_divs)} entries with profile enrichment")

        # Process each faculty entry
        for div in tqdm(extra_fields_divs, desc="Physics Faculty"):
            entry = {
                "name": "",
                "title": "",
                "email": "",
                "phone": "",
                "profile_url": "",
                "source_department": "Physics",
                "bio": "",
                "extra_info": ""
            }

            # Get basic info from listing page (same as before)
            item_container = div.find_parent('div', class_=lambda x: x and 'catItem' in str(x) if x else False)

            if item_container:
                name_elem = item_container.find(['h2', 'h3', 'h4'], class_=lambda x: x and 'catItemTitle' in str(x) if x else False)
                if name_elem:
                    name_link = name_elem.find('a')
                    entry['name'] = name_link.get_text().strip() if name_link else name_elem.get_text().strip()

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
                entry['extra_info'] = f"OFFICE:\n{office}\n\n"

            # Phone
            phone_match = re.search(r'Phone\s+(.+?)(?:\n|Web Page|$)', div_text)
            if phone_match:
                entry['phone'] = phone_match.group(1).strip()

            # Get profile URL
            web_links = div.find_all('a', href=True)
            for link in web_links:
                link_text = link.get_text().strip()
                href = link.get('href')

                if 'Department Profile' in link_text:
                    if href.startswith('http'):
                        entry['profile_url'] = href
                    else:
                        entry['profile_url'] = f'https://umdphysics.umd.edu{href}'
                    break

            # If we have a profile URL, visit it to get detailed info
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                # Append to existing extra_info
                if profile_details['extra_info']:
                    entry['extra_info'] += profile_details['extra_info']

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

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} Physics faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_physics_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    with_cv = sum(1 for f in faculty if 'CURRICULUM VITAE' in f.get('extra_info', ''))
    with_research = sum(1 for f in faculty if 'RESEARCH:' in f.get('extra_info', ''))
    with_teaching = sum(1 for f in faculty if 'TEACHING:' in f.get('extra_info', ''))
    with_news = sum(1 for f in faculty if 'NEWS:' in f.get('extra_info', ''))

    print(f"Faculty with biography: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")
    print(f"Faculty with CV link: {with_cv}/{len(faculty)}")
    print(f"Faculty with research info: {with_research}/{len(faculty)}")
    print(f"Faculty with teaching info: {with_teaching}/{len(faculty)}")
    print(f"Faculty with news: {with_news}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            print(f"  Extra info sections: {fac.get('extra_info', '')[:200]}...")
            break
