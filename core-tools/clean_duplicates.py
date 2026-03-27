"""
Script to remove duplicate faculty entries from cmns_faculty.db.

Strategy:
- Group by name and source_department
- For duplicates, keep the entry with bio data (enriched version)
- If neither has bio, keep the one with more extra_info
- Delete the older/less complete entries
"""

from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from collections import defaultdict
import logging

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


def clean_duplicates():
    """Remove duplicate faculty entries, keeping the most complete version."""

    engine = create_engine("sqlite:///../tools/cmns_faculty.db")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get all faculty
    all_faculty = session.query(CMNSFaculty).all()
    logging.info(f"Total faculty entries: {len(all_faculty)}")

    # Group by (name, department)
    faculty_groups = defaultdict(list)
    for fac in all_faculty:
        key = (fac.name, fac.source_department)
        faculty_groups[key].append(fac)

    # Find duplicates
    duplicates = {k: v for k, v in faculty_groups.items() if len(v) > 1}
    logging.info(f"Found {len(duplicates)} sets of duplicates")

    if not duplicates:
        logging.info("No duplicates found!")
        session.close()
        return

    # Process each duplicate group
    to_delete = []
    for (name, dept), entries in duplicates.items():
        logging.info(f"\nDuplicate: {name} ({dept}) - {len(entries)} entries")

        # Sort by completeness:
        # 1. Has bio (most important)
        # 2. Length of extra_info
        # 3. ID (newer is higher)
        def score_entry(entry):
            has_bio = 1 if entry.bio and len(entry.bio.strip()) > 0 else 0
            extra_len = len(entry.extra_info) if entry.extra_info else 0
            return (has_bio, extra_len, entry.id)

        entries_sorted = sorted(entries, key=score_entry, reverse=True)

        # Keep the best one, mark others for deletion
        keep = entries_sorted[0]
        delete = entries_sorted[1:]

        logging.info(f"  Keeping: ID={keep.id}, bio={bool(keep.bio)}, extra_info_len={len(keep.extra_info or '')}")
        for entry in delete:
            logging.info(f"  Deleting: ID={entry.id}, bio={bool(entry.bio)}, extra_info_len={len(entry.extra_info or '')}")
            to_delete.append(entry)

    # Delete duplicates
    if to_delete:
        logging.info(f"\nDeleting {len(to_delete)} duplicate entries...")
        for entry in to_delete:
            session.delete(entry)
        session.commit()
        logging.info("✓ Duplicates removed!")

    # Final count
    final_count = session.query(CMNSFaculty).count()
    logging.info(f"\nFinal faculty count: {final_count}")

    # Summary by department
    departments = session.query(CMNSFaculty.source_department).distinct().all()
    logging.info("\nFaculty by department:")
    for (dept,) in departments:
        count = session.query(CMNSFaculty).filter_by(source_department=dept).count()
        with_bio = session.query(CMNSFaculty).filter_by(source_department=dept).filter(CMNSFaculty.bio != None).filter(CMNSFaculty.bio != '').count()
        logging.info(f"  {dept}: {count} faculty, {with_bio} with bio ({100*with_bio//count if count > 0 else 0}%)")

    session.close()


if __name__ == "__main__":
    clean_duplicates()
