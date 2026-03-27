"""
Production scraper for A. James Clark School of Engineering faculty directories.
All Clark School departments use the same /clark/facultydir format.
"""

from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
import time
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

Base = declarative_base()

class ClarkFaculty(Base):
    __tablename__ = "clark_faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    title = Column(String(255))
    departments = Column(Text)  # Comma-separated list
    office = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    profile_url = Column(String(255))
    source_department = Column(String(255))  # Which Clark dept we scraped from
    bio = Column(Text)  # From Overview tab
    extra_info = Column(Text)  # From other tabs (research, teaching, news, etc.)


def scrape_faculty_profile(page, profile_url):
    """
    Visit a faculty profile page and extract bio and extra info.

    Args:
        page: Playwright page object
        profile_url: URL to the faculty profile

    Returns:
        Dictionary with 'bio' and 'extra_info' keys
    """
    result = {"bio": "", "extra_info": ""}

    try:
        page.goto(profile_url, wait_until="networkidle")
        time.sleep(1)

        # Extract bio from Overview tab (#faculty_overview)
        overview_div = page.query_selector("#faculty_overview")
        if overview_div:
            # Get all paragraph text
            paragraphs = overview_div.query_selector_all("p")
            bio_parts = []
            for p in paragraphs:
                text = p.inner_text().strip()
                if text:
                    bio_parts.append(text)
            result["bio"] = " ".join(bio_parts)

        # Extract extra info from other tabs
        extra_parts = []

        # Research Interests
        research_div = page.query_selector("#faculty_research_interests")
        if research_div:
            text = research_div.inner_text().strip()
            if text:
                extra_parts.append(f"RESEARCH INTERESTS:\n{text}")

        # Teaching
        teaching_div = page.query_selector("#faculty_teaching")
        if teaching_div:
            text = teaching_div.inner_text().strip()
            if text:
                extra_parts.append(f"TEACHING:\n{text}")

        # Publications (if available)
        pubs_div = page.query_selector("#faculty_publications")
        if pubs_div:
            text = pubs_div.inner_text().strip()
            if text:
                # Limit publications to first 1000 chars to avoid huge text
                if len(text) > 1000:
                    text = text[:1000] + "..."
                extra_parts.append(f"PUBLICATIONS:\n{text}")

        # Projects (if available)
        projects_div = page.query_selector("#faculty_projects")
        if projects_div:
            text = projects_div.inner_text().strip()
            if text:
                extra_parts.append(f"PROJECTS:\n{text}")

        result["extra_info"] = "\n\n".join(extra_parts)

    except Exception as e:
        logging.debug(f"Error scraping profile {profile_url}: {e}")

    return result


def scrape_clark_directory(page, url, department_name):
    """
    Scrape a single Clark School faculty directory page.

    Args:
        page: Playwright page object
        url: Full URL to the faculty directory
        department_name: Name of the department for logging

    Returns:
        List of faculty dictionaries
    """
    faculty_list = []

    logging.info(f"Scraping {department_name} from {url}")

    try:
        # Navigate to the page
        page.goto(url, wait_until="networkidle")
        time.sleep(2)

        # Find all faculty rows
        faculty_rows = page.query_selector_all("div.faculty_row")
        logging.info(f"Found {len(faculty_rows)} faculty members in {department_name}")

        for row in tqdm(faculty_rows, desc=f"{department_name[:20]}"):
            try:
                faculty = {"source_department": department_name}

                # Name and profile URL
                name_link = row.query_selector("div.field-directory-name-title-wrapper a")
                if name_link:
                    faculty["name"] = name_link.inner_text().strip()
                    href = name_link.get_attribute("href")
                    if href:
                        # Make it a full URL if it's relative
                        if href.startswith("/"):
                            faculty["profile_url"] = f"https://faculty.eng.umd.edu{href}"
                        else:
                            faculty["profile_url"] = href

                # Title
                title_h3 = row.query_selector("div.title-wrapper h3")
                if title_h3:
                    faculty["title"] = title_h3.inner_text().strip()

                # Departments (multiple possible)
                dept_links = row.query_selector_all("div.field-directory-dept-contact-wrapper > a")
                if dept_links:
                    depts = [link.inner_text().strip() for link in dept_links]
                    faculty["departments"] = ", ".join(depts)

                # Contact wrapper has office, email, phone
                contact_div = row.query_selector("div.contact-wrapper")
                if contact_div:
                    # Office is first h3
                    office_h3s = contact_div.query_selector_all("h3")
                    if office_h3s:
                        # First h3 without a link is usually the office
                        for h3 in office_h3s:
                            if not h3.query_selector("a"):
                                faculty["office"] = h3.inner_text().strip()
                                break

                    # Email
                    email_link = contact_div.query_selector("a[href^='mailto:']")
                    if email_link:
                        faculty["email"] = email_link.inner_text().strip()

                    # Phone
                    phone_link = contact_div.query_selector("a[href^='tel:']")
                    if phone_link:
                        faculty["phone"] = phone_link.inner_text().strip()

                # Only add if we got at least a name
                if faculty.get("name"):
                    faculty_list.append(faculty)

            except Exception as e:
                logging.error(f"Error parsing faculty row: {e}")
                continue

        # Now visit each profile page to get bio and extra info
        logging.info(f"\nFetching detailed profiles for {department_name}...")
        for faculty in tqdm(faculty_list, desc=f"{department_name[:20]} profiles"):
            if faculty.get("profile_url"):
                profile_data = scrape_faculty_profile(page, faculty["profile_url"])
                faculty["bio"] = profile_data["bio"]
                faculty["extra_info"] = profile_data["extra_info"]
                time.sleep(0.5)  # Be polite to the server

    except Exception as e:
        logging.error(f"Error scraping {department_name}: {e}")

    return faculty_list


def scrape_all_clark_departments():
    """Scrape all Clark School engineering departments."""

    # List of Clark School departments
    clark_departments = [
        ("https://faculty.eng.umd.edu/?drfilter=1", "Engineering General"),
        ("https://bioe.umd.edu/clark/facultydir?drfilter=1", "Bioengineering"),
        ("https://me.umd.edu/clark/facultydir?drfilter=1", "Mechanical Engineering"),
        ("https://ece.umd.edu/clark/facultydir?drfilter=1", "Electrical & Computer Engineering"),
        ("https://cee.umd.edu/clark/facultydir?drfilter=1", "Civil & Environmental Engineering"),
        ("https://aero.umd.edu/clark/facultydir?drfilter=1", "Aerospace Engineering"),
        ("https://chbe.umd.edu/clark/facultydir?drfilter=1", "Chemical & Biomolecular Engineering"),
    ]

    # Setup database
    engine = create_engine("sqlite:///../tools/clark_faculty.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    all_faculty = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for url, dept_name in clark_departments:
            faculty_list = scrape_clark_directory(page, url, dept_name)
            all_faculty.extend(faculty_list)
            logging.info(f"Scraped {len(faculty_list)} faculty from {dept_name}")
            time.sleep(2)  # Be polite to the server

        browser.close()

    # Save to database
    logging.info(f"\nSaving {len(all_faculty)} faculty to database...")
    for fac in tqdm(all_faculty, desc="Saving to DB"):
        session.add(ClarkFaculty(**fac))

    session.commit()
    session.close()

    logging.info(f"✓ Complete! Scraped {len(all_faculty)} total faculty members")
    return all_faculty


if __name__ == "__main__":
    faculty = scrape_all_clark_departments()

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total faculty scraped: {len(faculty)}")

    # Count bios
    with_bio = sum(1 for f in faculty if f.get('bio'))
    with_extra = sum(1 for f in faculty if f.get('extra_info'))
    print(f"Faculty with bios: {with_bio}/{len(faculty)}")
    print(f"Faculty with extra info: {with_extra}/{len(faculty)}")

    print(f"\nSample entries:")
    for fac in faculty[:3]:
        print(f"\n  Name: {fac.get('name')}")
        print(f"  Title: {fac.get('title')}")
        print(f"  Email: {fac.get('email')}")
        print(f"  Department: {fac.get('source_department')}")
        bio = fac.get('bio', '')
        if bio:
            print(f"  Bio: {bio[:150]}..." if len(bio) > 150 else f"  Bio: {bio}")
        extra = fac.get('extra_info', '')
        if extra:
            print(f"  Extra info length: {len(extra)} chars")
