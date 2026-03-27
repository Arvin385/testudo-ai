"""
Master script to run all CMNS faculty scrapers.

This script orchestrates the execution of all individual department scrapers
for the College of Computer, Mathematical, and Natural Sciences (CMNS).

Usage:
    python run_all_cmns_scrapers.py                    # Run all scrapers
    python run_all_cmns_scrapers.py --departments physics biology  # Run specific departments
"""

import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Import all scraper functions
try:
    from scrape_physics_enriched import scrape_physics_enriched
    from scrape_biology_enriched import scrape_biology_enriched
    from scrape_math_faculty import scrape_physics_faculty as scrape_math_faculty  # Uses same function name
    from scrape_chemistry_enriched import scrape_chemistry_enriched
    from scrape_astronomy_enriched import scrape_astronomy_enriched
    from scrape_geology_enriched import scrape_geology_enriched
    from scrape_aosc_enriched import scrape_aosc_enriched
except ImportError as e:
    logging.error(f"Failed to import scraper modules: {e}")
    logging.error("Make sure all scraper files are in the same directory.")
    sys.exit(1)


# Define all available scrapers
SCRAPERS = {
    'physics': {
        'name': 'Physics',
        'function': scrape_physics_enriched,
        'enriched': True,
        'expected_count': 182
    },
    'biology': {
        'name': 'Biology',
        'function': scrape_biology_enriched,
        'enriched': True,
        'expected_count': 39
    },
    'mathematics': {
        'name': 'Mathematics',
        'function': scrape_math_faculty,
        'enriched': False,
        'expected_count': 88
    },
    'chemistry': {
        'name': 'Chemistry & Biochemistry',
        'function': scrape_chemistry_enriched,
        'enriched': True,
        'expected_count': 34
    },
    'astronomy': {
        'name': 'Astronomy',
        'function': scrape_astronomy_enriched,
        'enriched': True,
        'expected_count': 13
    },
    'geology': {
        'name': 'Geology',
        'function': scrape_geology_enriched,
        'enriched': True,
        'expected_count': 30
    },
    'aosc': {
        'name': 'Atmospheric & Oceanic Science',
        'function': scrape_aosc_enriched,
        'enriched': True,
        'expected_count': 17
    }
}


def run_scraper(scraper_key):
    """
    Run a single scraper and return results.

    Args:
        scraper_key: Key from SCRAPERS dict

    Returns:
        dict: Results including faculty count, success status, etc.
    """
    scraper_info = SCRAPERS[scraper_key]

    logging.info("="*80)
    logging.info(f"Starting scraper: {scraper_info['name']}")
    logging.info(f"Enriched: {'Yes' if scraper_info['enriched'] else 'No'}")
    logging.info(f"Expected count: ~{scraper_info['expected_count']} faculty")
    logging.info("="*80)

    try:
        start_time = datetime.now()

        # Run the scraper
        faculty_list = scraper_info['function']()

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        result = {
            'department': scraper_info['name'],
            'success': True,
            'count': len(faculty_list),
            'expected': scraper_info['expected_count'],
            'duration': duration,
            'enriched': scraper_info['enriched']
        }

        logging.info(f"✓ {scraper_info['name']} completed successfully")
        logging.info(f"  Scraped: {result['count']} faculty")
        logging.info(f"  Duration: {duration:.1f} seconds")

        return result

    except Exception as e:
        logging.error(f"✗ {scraper_info['name']} failed: {e}")
        return {
            'department': scraper_info['name'],
            'success': False,
            'count': 0,
            'expected': scraper_info['expected_count'],
            'error': str(e),
            'enriched': scraper_info['enriched']
        }


def print_summary(results):
    """Print a summary of all scraping results."""
    print("\n" + "="*80)
    print("SCRAPING SUMMARY")
    print("="*80)

    total_faculty = 0
    successful = 0
    failed = 0

    for result in results:
        status = "✓" if result['success'] else "✗"
        enriched = " [ENRICHED]" if result['enriched'] else ""

        if result['success']:
            successful += 1
            total_faculty += result['count']
            print(f"{status} {result['department']}{enriched}")
            print(f"    Scraped: {result['count']} faculty (expected ~{result['expected']})")
            print(f"    Duration: {result['duration']:.1f}s")
        else:
            failed += 1
            print(f"{status} {result['department']}{enriched}")
            print(f"    Error: {result.get('error', 'Unknown error')}")

    print("\n" + "-"*80)
    print(f"Total departments processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total faculty scraped: {total_faculty}")
    print("="*80)


def main():
    """Main execution function."""
    start_time = datetime.now()

    # Determine which scrapers to run
    departments_to_run = []

    if len(sys.argv) > 1 and '--departments' in sys.argv:
        # Run specific departments
        try:
            dept_index = sys.argv.index('--departments')
            departments_to_run = sys.argv[dept_index + 1:]

            # Validate department names
            invalid = [d for d in departments_to_run if d not in SCRAPERS]
            if invalid:
                logging.error(f"Invalid department names: {invalid}")
                logging.info(f"Valid options: {', '.join(SCRAPERS.keys())}")
                sys.exit(1)

            logging.info(f"Running scrapers for: {', '.join(departments_to_run)}")
        except (ValueError, IndexError):
            logging.error("Invalid --departments argument")
            sys.exit(1)
    else:
        # Run all scrapers
        departments_to_run = list(SCRAPERS.keys())
        logging.info("Running ALL CMNS scrapers")

    logging.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("")

    # Run scrapers
    results = []
    for dept_key in departments_to_run:
        result = run_scraper(dept_key)
        results.append(result)
        print()  # Blank line between departments

    # Print summary
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()

    print_summary(results)
    print(f"\nTotal execution time: {total_duration/60:.1f} minutes")
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Exit with appropriate code
    failed_count = sum(1 for r in results if not r['success'])
    sys.exit(failed_count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
