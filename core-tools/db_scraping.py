# This file is NOT A TOOL, it's something we will: 
# USE ONCE IN A WHILE TO UPDATE LOCAL DB

from playwright.sync_api import sync_playwright
import requests
import feedparser
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime,
    ForeignKey, Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from enum import Enum as PyEnum
import time
import re

# Progress & Log bar imports and initial configuration:
import logging
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s"
)

Base = declarative_base()

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True)
    url = Column(String(255))
    faculty = relationship("Faculty", back_populates="department")

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), index=True)
    title_department = Column(String(255))
    degrees = Column(Text)
    email = Column(String(255))
    phone = Column(String(50))
    bio = Column(Text)
    department = relationship("Department", back_populates="faculty")

class Calendar(Base):
    __tablename__ = "calendar"
    id = Column(Integer, primary_key=True)
    term = Column(String(255), index=True)
    event = Column(String(255))
    date = Column(String(255))

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), index=True)
    url = Column(String(255))
    type = Column(String)
    description = Column(Text)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), index=True)
    link = Column(String(255))
    summary = Column(Text)
    date = Column(DateTime, index=True)
    __table_args__ = (UniqueConstraint("title", "date", name="_alert_uc"),)

# Optional multi-column index for frequent queries
Index("ix_faculty_dept_name", Faculty.department_id, Faculty.name)


def lookup_faculty_contact(page, name):
    """
    Look up a faculty member's email and phone via UMD directory search.
    Uses the identity.umd.edu/search page with Playwright to submit a search
    and parse the results.

    Returns a dict with 'email' and 'phone' keys (empty strings if not found).
    """
    email = ""
    phone = ""

    try:
        # Parse the name - try to handle "Last, First" format
        name_parts = name.split(",")
        if len(name_parts) >= 2:
            last_name = name_parts[0].strip()
            first_name = name_parts[1].strip().split()[0]  # first word only
            search_name = f"{first_name} {last_name}"
        else:
            search_name = name.strip()

        page.goto("https://identity.umd.edu/search", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Use basic search - it's simpler and more reliable
        basic_input = page.query_selector("input[name='basicSearchInput']")
        if basic_input:
            basic_input.fill(search_name)

            # Submit the search
            submit_btn = page.query_selector("input[name='basicSearch']")
            if submit_btn:
                submit_btn.click()
            else:
                page.keyboard.press("Enter")
        else:
            logging.debug(f"Could not find basic search input for {name}")
            return {"email": email, "phone": phone}

        # Wait for results to load
        page.wait_for_timeout(2000)

        # Look for result items with the new structure
        result_items = page.query_selector_all("div.DisplaySearchItem")

        if not result_items:
            logging.debug(f"No results found for {name}")
            return {"email": email, "phone": phone}

        # Take the first result (assuming it's the most relevant)
        for item in result_items[:1]:
            # Extract email from div.email a[href^='mailto:']
            email_div = item.query_selector("div.email a")
            if email_div:
                email_href = email_div.get_attribute("href")
                if email_href:
                    email = email_href.replace("mailto:", "").strip()
                else:
                    email = email_div.inner_text().strip()

            # Extract phone from div.phoneNumbers
            phone_div = item.query_selector("div.phoneNumbers")
            if phone_div:
                phone_text = phone_div.inner_text().strip()
                # Remove "Phone:" prefix and check for "Not Published"
                phone_text = phone_text.replace("Phone:", "").strip()
                if "Not Published" not in phone_text and phone_text:
                    phone = phone_text

    except Exception as e:
        logging.debug(f"Directory lookup failed for {name}: {e}")

    return {"email": email, "phone": phone}


def lookup_faculty_bio(page, name, department_hint=""):
    """
    Attempt to find a short bio for a faculty member by searching
    their name on Google Scholar or the UMD website.

    Tries department-specific faculty pages first, then falls back
    to a general UMD search.

    Returns a bio string (empty if not found).
    """
    bio = ""

    try:
        # Try searching the UMD site for the faculty member's profile
        search_query = f"{name} site:umd.edu faculty"
        page.goto(
            f"https://www.google.com/search?q={requests.utils.quote(search_query)}",
            wait_until="networkidle"
        )
        page.wait_for_timeout(1500)

        # Get the first result link that looks like a faculty profile
        result_links = page.query_selector_all("div.g a[href]")
        profile_url = ""
        for link in result_links[:5]:
            href = link.get_attribute("href") or ""
            # Look for faculty profile URLs (common patterns)
            if any(pattern in href for pattern in [
                "/faculty/", "/people/", "/directory/", "/profile/",
                "/about/faculty", "/our-faculty"
            ]) and "umd.edu" in href:
                profile_url = href
                break

        if profile_url:
            page.goto(profile_url, wait_until="networkidle")
            page.wait_for_timeout(1500)

            # Try to extract bio from common selectors on faculty profile pages
            bio_selectors = [
                "div.field-name-body",           # Drupal body field
                "div.biography",                  # Common bio class
                "div.bio",
                "section.biography",
                "div#biography",
                "div.faculty-bio",
                "div.profile-bio",
                "div.about-text",
                "div.field--name-body",           # Drupal 8+
                "article .content p",             # Generic article content
                "div.profile-content p",
                "div.entry-content p",
                "main p",                         # Broad fallback
            ]

            for selector in bio_selectors:
                elements = page.query_selector_all(selector)
                if elements:
                    paragraphs = []
                    for el in elements[:3]:  # Limit to first 3 paragraphs
                        text = el.inner_text().strip()
                        if len(text) > 50:  # Skip very short fragments
                            paragraphs.append(text)
                    if paragraphs:
                        bio = " ".join(paragraphs)
                        # Truncate to a reasonable length for a "short bio"
                        if len(bio) > 1000:
                            bio = bio[:997] + "..."
                        break

    except Exception as e:
        logging.debug(f"Bio lookup failed for {name}: {e}")

    return bio


def umd_unified_scraper():
    """
    Unified scraper for all UMD data categories.
    Returns a structured dictionary summarizing the results.
    Progress and log bars as scraper updates/creates database
    """
    try:
        logging.info("Starting scraper...")

        engine = create_engine("sqlite:///../tools/testudo_data.db")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        stats = {
            "calendar": 0,
            "faculty": 0,
            "faculty_with_email": 0,
            "faculty_with_bio": 0,
            "departments": 0,
            "programs": 0,
            "alerts": 0
        }

        # 1. Academic Calendar
        # Start logging
        logging.info("Scraping academic calendar...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                "https://academiccatalog.umd.edu/about-university/academic-calendar/semester-calendar/",
                wait_until="networkidle"
            )
            page.wait_for_selector("table.sc_sctable tbody tr")

            semester_tables = page.query_selector_all("table.sc_sctable")

            # Continuous update log
            for table in tqdm(semester_tables, desc="Calendar sections"):
                term = table.evaluate("table => table.previousElementSibling.textContent.trim()")
                rows = table.query_selector_all("tbody tr")

                for row in rows:
                    event = row.query_selector("td.column0").inner_text().strip()
                    date = row.query_selector("td.column1").inner_text().strip()
                    session.add(Calendar(term=term, event=event, date=date))
                    stats["calendar"] += 1
            
            browser.close()
        # Print final log for category
        logging.info(f"Calendar events scraped: {stats['calendar']}")

        # 2. Faculty Directory (with contact info and bio)
        logging.info("Scraping faculty directory...")
        with sync_playwright() as p:
            # Check if auth state exists
            auth_file = "umd_auth_state.json"
            import os

            if os.path.exists(auth_file):
                logging.info(f"Using saved authentication from {auth_file}")
                browser = p.chromium.launch(headless=True)
                # Create context with saved auth state
                context = browser.new_context(storage_state=auth_file)
            else:
                logging.warning(f"No auth file found at {auth_file}")
                logging.warning("Contact/bio lookup may fail. Run login_umd.py first!")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()

            # Page for catalog scraping
            catalog_page = context.new_page()
            catalog_page.goto(
                "https://academiccatalog.umd.edu/undergraduate/administrators-officials-faculty/", 
                wait_until="networkidle"
            )

            faculty_elements = catalog_page.query_selector_all("p.keeptogether.faculty-item")

            # Collect basic faculty data first
            # LIMIT TO FIRST 10 FOR TESTING
            faculty_data = []
            for idx, el in enumerate(tqdm(faculty_elements[:10], desc="Faculty entries (basic)")):
                name = el.query_selector("strong").inner_text().strip()
                full_text = el.inner_text().strip()
                rest = full_text.replace(name, "").strip(" ;\n")

                # Degree parsing
                if any(x in rest for x in ["Ph.D.", "B.A.", "M.A.", "M.S."]):
                    parts = rest.split(";")
                    title_dept = parts[0].strip()
                    degrees = ";".join(parts[1:]).strip()
                else:
                    title_dept, degrees = rest, ""

                faculty_data.append({
                    "name": name,
                    "title_department": title_dept,
                    "degrees": degrees
                })

            logging.info(f"LIMITED TEST MODE: Processing only {len(faculty_data)} faculty members")

            catalog_page.close()

            # Now enrich each faculty member with contact info from UMD directory
            logging.info("Enriching faculty with contact info from UMD directory...")
            directory_page = context.new_page()

            for entry in tqdm(faculty_data, desc="Faculty contact lookup"):
                contact = lookup_faculty_contact(directory_page, entry["name"])
                logging.debug(f"CONTACT FOUND for {entry['name']}: {contact}")
                entry["email"] = contact["email"]
                entry["phone"] = contact["phone"]

                if contact["email"]:
                    stats["faculty_with_email"] += 1

                # Be polite to the server (reduced for testing)
                time.sleep(0.2)

            directory_page.close()

            # Look up bios (this is slower, so we log separately)
            logging.info("Looking up faculty bios...")
            bio_page = context.new_page()

            for entry in tqdm(faculty_data, desc="Faculty bio lookup"):
                bio = lookup_faculty_bio(bio_page, entry["name"], entry.get("title_department", ""))
                entry["bio"] = bio

                if bio:
                    stats["faculty_with_bio"] += 1

                # Be polite to Google and UMD servers (reduced for testing)
                time.sleep(0.3)

            bio_page.close()

            # Save all faculty to DB
            for entry in faculty_data:
                session.add(Faculty(
                    name=entry["name"],
                    title_department=entry["title_department"],
                    degrees=entry["degrees"],
                    email=entry["email"],
                    phone=entry["phone"],
                    bio=entry["bio"]
                ))
                stats["faculty"] += 1

            context.close()
            browser.close()
        logging.info(f"Faculty scraped: {stats['faculty']} "
                     f"(with email: {stats['faculty_with_email']}, "
                     f"with bio: {stats['faculty_with_bio']})")

        # 3. Departments (with upsert and no autoflush)
        logging.info("Scraping departments...")
        with session.no_autoflush:

            # prevents SQLAlchemy from flushing mid-loop, avoiding IntegrityError
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto("https://umd.edu/academic-departments-and-programs")
                page.wait_for_selector("div.umd-text-rich-advanced ul li a")

                department_links = page.query_selector_all("div.umd-text-rich-advanced ul li a")
                
                for link in department_links:
                    name = link.inner_text().strip()
                    url = link.get_attribute("href").strip()

                    # upsert logic (upsert = update and insert)
                    existing = session.query(Department).filter_by(name=name).first()

                    if existing:
                        existing.url = url   # update instead of insert
                    else:
                        session.add(Department(name=name, url=url))
                        stats["departments"] += 1
                
                browser.close()
        logging.info(f"Departments scraped/updated: {stats['departments']}")

        # 4. Majors & Minors (also upsert)
        logging.info("Scraping majors & minors...")
        with session.no_autoflush:

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto("https://admissions.umd.edu/programs")
                page.wait_for_selector("div.entry-list div.list div")

                program_divs = page.query_selector_all("div.entry-list div.list div")
                for div in tqdm(program_divs, desc="Programs"):
                    a_tag = div.query_selector("h3 a")
                    
                    name = a_tag.inner_text().strip() if a_tag else ""
                    url = a_tag.get_attribute("href") if a_tag else ""
                    
                    type_tags = div.query_selector_all("div.types span")
                    types = ", ".join([t.inner_text().strip() for t in type_tags])
                    
                    desc_tag = div.query_selector("div.rich-text p")
                    description = desc_tag.inner_text().strip() if desc_tag else ""
                    
                    # upsert program
                    existing = session.query(Program).filter_by(name=name).first()
                    if existing:
                        existing.url = url
                        existing.type = types
                        existing.description = description
                    else:
                        session.add(Program(
                            name=name,
                            url=url,
                            type=types,
                            description=description
                        ))
                        stats["programs"] += 1

                browser.close()
        logging.info(f"Programs scraped: {stats['programs']}")

        # 5. UMD Alerts (RSS)
        logging.info("Scraping UMD alert RSS feed...")
        RSS_URL = "https://alert.umd.edu/rss.xml"
        try:
            r = requests.get(RSS_URL, timeout=10)
            r.raise_for_status()
            feed = feedparser.parse(r.content)

            for entry in tqdm(feed.entries, desc="Alerts"):
                title = entry.title
                link = entry.link
                summary = entry.get("description", "")
                date = datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else datetime.now()
                
                if not session.query(Alert).filter_by(title=title).first():
                    session.add(Alert(
                        title=title, 
                        link=link, 
                        summary=summary, 
                        date=date))
                    
                    stats["alerts"] += 1

            logging.info(f"Alerts scraped: {stats['alerts']}")
        except Exception as e:
            logging.error(f"Alert RSS error: {e}")
            stats["alerts_error"] = str(e)

        # commit changes
        session.commit()
        session.close()

        # Final log
        logging.info("Scraping completed successfully!")

        return {
            "status": "success",
            "message": "UMD data scraped and stored successfully.",
            "database": "testudo_data.db",
            "stats": stats
        }

    except Exception as e:
        # Log failed session
        logging.error(f"Scraper crashed: {e}")
        # always rollback session if there's an error
        session.rollback()
        return {"status": "error", "error_message": str(e)}

if __name__ == "__main__":
    res = umd_unified_scraper()
    print(res)