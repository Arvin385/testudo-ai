"""
Enhanced scraper for UMD Chemistry & Biochemistry Department faculty with biographical information.

This scraper:
1. Clicks "View All" on the main people page to load all faculty
2. Collects basic info from faculty cards (name, email, title)
3. Visits each faculty profile URL to extract detailed information:
   - Research Interests
   - Education
   - Professional Experience
   - Professional Societies
   - Major Recognitions and Honors
   - Significant Professional Service
   - Research Students Mentored
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
    Visit a Chemistry faculty profile page and extract detailed information.

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

        # Find the main body div with content
        body_divs = soup.find_all('div', class_='field--name-body')
        content_div = None
        for div in body_divs:
            text = div.get_text().strip()
            if len(text) > 100 and ('Biography' in text or 'Research' in text or 'Education' in text):
                content_div = div
                break

        if content_div:
            # Get all text content
            all_text = content_div.get_text('\n', strip=True)

            # Extract Research Interests (main bio)
            research_match = re.search(
                r'Research Interest[s]?[:\s]*(.+?)(?=\n(?:Professional Societies|Education|Major Recognitions|Significant Professional|Research Students|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if research_match:
                result['bio'] = research_match.group(1).strip()

            # Extract Education
            edu_match = re.search(
                r'Education[:\s]*(.+?)(?=\n(?:Professional Experience|Research Interest|Professional Societies|Major Recognitions|Significant Professional|Research Students|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if edu_match:
                edu_text = edu_match.group(1).strip()
                if edu_text:
                    extra_sections.append(f"EDUCATION:\n{edu_text}")

            # Extract Professional Experience
            exp_match = re.search(
                r'Professional Experience[:\s]*(.+?)(?=\n(?:Research Interest|Professional Societies|Major Recognitions|Significant Professional|Research Students|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if exp_match:
                exp_text = exp_match.group(1).strip()
                if exp_text:
                    extra_sections.append(f"PROFESSIONAL EXPERIENCE:\n{exp_text}")

            # Extract Professional Societies
            societies_match = re.search(
                r'Professional Societies[:\s]*(.+?)(?=\n(?:Major Recognitions|Significant Professional|Research Students|Research Interest|Education|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if societies_match:
                societies_text = societies_match.group(1).strip()
                if societies_text:
                    extra_sections.append(f"PROFESSIONAL SOCIETIES:\n{societies_text}")

            # Extract Major Recognitions and Honors
            honors_match = re.search(
                r'Major Recognitions and Honors[:\s]*(.+?)(?=\n(?:Significant Professional|Research Students|Professional Societies|Research Interest|Education|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if honors_match:
                honors_text = honors_match.group(1).strip()
                if honors_text:
                    extra_sections.append(f"MAJOR RECOGNITIONS AND HONORS:\n{honors_text}")

            # Extract Significant Professional Service
            service_match = re.search(
                r'Significant Professional Service and Activities[:\s]*(.+?)(?=\n(?:Research Students|Major Recognitions|Professional Societies|Research Interest|Education|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if service_match:
                service_text = service_match.group(1).strip()
                if service_text:
                    extra_sections.append(f"SIGNIFICANT PROFESSIONAL SERVICE:\n{service_text}")

            # Extract Research Students Mentored
            students_match = re.search(
                r'Research Students Mentored[:\s]*(.+?)(?=\n(?:Major Recognitions|Significant Professional|Professional Societies|Research Interest|Education|$))',
                all_text,
                re.DOTALL | re.IGNORECASE
            )
            if students_match:
                students_text = students_match.group(1).strip()
                if students_text:
                    extra_sections.append(f"RESEARCH STUDENTS MENTORED:\n{students_text}")

        # Combine all extra sections
        if extra_sections:
            result['extra_info'] = "\n\n".join(extra_sections)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")
        # Don't fail the whole process, just return empty results

    return result


def scrape_chemistry_enriched():
    """Scrape Chemistry faculty with enriched biographical information."""

    # Setup database
    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        logging.info("Fetching Chemistry faculty listing...")
        page.goto('https://chem.umd.edu/people', wait_until='networkidle')
        time.sleep(2)

        # Click "View All" to load all faculty
        try:
            logging.info("Clicking 'View All'...")
            view_all = page.query_selector('a:has-text("View All")')
            if view_all:
                view_all.click()
                page.wait_for_load_state('networkidle')
                time.sleep(3)
        except Exception as e:
            logging.warning(f"Could not click View All: {e}")

        # Get the HTML content
        html = page.content()

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find all faculty profile links
        faculty_entries = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            # Profile links have hyphens and are under /people/
            if href and '/people/' in href and '-' in href and len(text) > 5:
                # Make sure it's not a navigation link (those are just /people/a, etc.)
                if not re.match(r'^/people/[a-z]$', href):
                    faculty_entries.append((text, href))

        # Remove duplicates
        seen = set()
        unique_faculty = []
        for name, url in faculty_entries:
            if url not in seen:
                seen.add(url)
                unique_faculty.append((name, url))

        logging.info(f"Found {len(unique_faculty)} potential faculty entries")
        logging.info(f"Processing all {len(unique_faculty)} entries with profile enrichment")

        # Process each faculty entry
        for name, profile_path in tqdm(unique_faculty, desc="Chemistry Faculty"):
            entry = {
                "name": name,
                "title": "",
                "email": "",
                "phone": "",
                "profile_url": "",
                "source_department": "Chemistry & Biochemistry",
                "bio": "",
                "extra_info": ""
            }

            # Convert to absolute URL
            if profile_path.startswith('http'):
                entry['profile_url'] = profile_path
            else:
                entry['profile_url'] = f'https://chem.umd.edu{profile_path}'

            # Visit profile to get all info including email
            if entry['profile_url']:
                profile_details = scrape_profile_details(page, entry['profile_url'])
                entry['bio'] = profile_details['bio']
                entry['extra_info'] = profile_details['extra_info']

                # Also extract basic info from profile page
                html = page.content()
                soup = BeautifulSoup(html, 'html.parser')

                # Extract email
                email_link = soup.find('a', href=lambda x: x and 'mailto:' in x if x else False)
                if email_link:
                    entry['email'] = email_link.get('href').replace('mailto:', '')

                # Extract title
                title_div = soup.find('div', class_='field--name-field-classification')
                if title_div:
                    entry['title'] = title_div.get_text().strip()

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

    logging.info(f"Complete! Scraped {len(all_faculty)} Chemistry faculty members with enriched data")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_chemistry_enriched()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count data fields
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    with_email = sum(1 for f in faculty if f.get('email'))
    with_education = sum(1 for f in faculty if 'EDUCATION:' in f.get('extra_info', ''))
    with_experience = sum(1 for f in faculty if 'PROFESSIONAL EXPERIENCE:' in f.get('extra_info', ''))
    with_honors = sum(1 for f in faculty if 'HONORS:' in f.get('extra_info', ''))

    print(f"Faculty with research interests: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")
    print(f"Faculty with email: {with_email}/{len(faculty)}")
    print(f"Faculty with education: {with_education}/{len(faculty)}")
    print(f"Faculty with experience: {with_experience}/{len(faculty)}")
    print(f"Faculty with honors: {with_honors}/{len(faculty)}")

    print(f"\nSample entry with bio:")
    for fac in faculty:
        if fac.get('bio'):
            print(f"\n  Name: {fac.get('name')}")
            print(f"  Email: {fac.get('email')}")
            print(f"  Bio: {fac.get('bio')[:200]}...")
            print(f"  Extra info preview: {fac.get('extra_info', '')[:200]}...")
            break
