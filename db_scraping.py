TOOL_SPEC = {
    "name": "db_scraping",
    "description": (
        "Scrapes academic data from sites from the University of Maryland including "
        "academic calendar, faculty directory, departments, programs, and alerts, "
        "and stores all data in a unified SQLite database."
    ),
    "parameters": []
}

from playwright.sync_api import sync_playwright
import requests
import feedparser
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Calendar(Base):
    __tablename__ = "calendar"
    id = Column(Integer, primary_key=True)
    term = Column(String)
    event = Column(String)
    date = Column(String)

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    title_department = Column(Text)
    degrees = Column(Text)

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)

class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    url = Column(String)
    type = Column(String)
    description = Column(Text)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)
    summary = Column(Text)
    date = Column(DateTime)


def umd_unified_scraper():
    """
    Unified scraper for all UMD data categories.
    Returns a structured dictionary summarizing the results.
    """
    try:
        engine = create_engine("sqlite:///testudo_data.db")
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
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(
                "https://academiccatalog.umd.edu/about-university/academic-calendar/semester-calendar/",
                wait_until="networkidle"
            )
            page.wait_for_selector("table.sc_sctable tbody tr")

            semester_tables = page.query_selector_all("table.sc_sctable")
            for table in semester_tables:
                term = table.evaluate("table => table.previousElementSibling.textContent.trim()")
                rows = table.query_selector_all("tbody tr")
                for row in rows:
                    event = row.query_selector("td.column0").inner_text().strip()
                    date = row.query_selector("td.column1").inner_text().strip()
                    session.add(Calendar(term=term, event=event, date=date))
                    stats["calendar"] += 1
            browser.close()

        # 2. Faculty Directory
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://academiccatalog.umd.edu/undergraduate/administrators-officials-faculty/", wait_until="networkidle")

            faculty_elements = page.query_selector_all("p.keeptogether.faculty-item")
            for el in faculty_elements:
                name = el.query_selector("strong").inner_text().strip()
                full_text = el.inner_text().strip()
                rest = full_text.replace(name, "").strip(" ;\n")
                if any(x in rest for x in ["Ph.D.", "B.A.", "M.A.", "M.S."]):
                    parts = rest.split(";")
                    title_dept = parts[0].strip()
                    degrees = ";".join(parts[1:]).strip()
                else:
                    title_dept, degrees = rest, ""
                session.add(Faculty(name=name, title_department=title_dept, degrees=degrees))
                stats["faculty"] += 1
            browser.close()

        # 3. Departments amd Programs
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://umd.edu/academic-departments-and-programs")
            page.wait_for_selector("div.umd-text-rich-advanced ul li a")

            department_links = page.query_selector_all("div.umd-text-rich-advanced ul li a")
            for link in department_links:
                name = link.inner_text().strip()
                url = link.get_attribute("href").strip()
                session.add(Department(name=name, url=url))
                stats["departments"] += 1
            browser.close()

        # 4. Majors & Minors
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://admissions.umd.edu/programs")
            page.wait_for_selector("div.entry-list div.list div")

            program_divs = page.query_selector_all("div.entry-list div.list div")
            for div in program_divs:
                a_tag = div.query_selector("h3 a")
                name = a_tag.inner_text().strip() if a_tag else ""
                url = a_tag.get_attribute("href") if a_tag else ""
                type_tags = div.query_selector_all("div.types span")
                types = ", ".join([t.inner_text().strip() for t in type_tags])
                desc_tag = div.query_selector("div.rich-text p")
                description = desc_tag.inner_text().strip() if desc_tag else ""
                session.add(Program(name=name, url=url, type=types, description=description))
                stats["programs"] += 1
            browser.close()

        # 5. UMD Alerts (RSS)
        RSS_URL = "https://alert.umd.edu/rss.xml"
        try:
            r = requests.get(RSS_URL, timeout=10)
            r.raise_for_status()
            feed = feedparser.parse(r.content)

            for entry in feed.entries:
                title = entry.title
                link = entry.link
                summary = entry.get("description", "")
                date = datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else datetime.now()
                if not session.query(Alert).filter_by(title=title).first():
                    session.add(Alert(title=title, link=link, summary=summary, date=date))
                    stats["alerts"] += 1
        except Exception as e:
            stats["alerts_error"] = str(e)

        session.commit()
        session.close()

        return {
            "status": "success",
            "message": "UMD data scraped and stored successfully.",
            "database": "testudo_data.db",
            "stats": stats
        }

    except Exception as e:
        return {"status": "error", "error_message": str(e)}
if __name__ == "__main__":
    res = umd_unified_scraper()
    print(res)
