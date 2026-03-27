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


