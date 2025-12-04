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

        # 2. Faculty Directory
        logging.info("Scraping faculty directory...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                "https://academiccatalog.umd.edu/undergraduate/administrators-officials-faculty/", 
                wait_until="networkidle"
                )

            faculty_elements = page.query_selector_all("p.keeptogether.faculty-item")

            for el in tqdm(faculty_elements, desc="Faculty entries"):
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
                
                session.add(Faculty(name=name, title_department=title_dept, degrees=degrees))
                stats["faculty"] += 1

            browser.close()
        logging.info(f"Faculty scraped: {stats['faculty']}")

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
