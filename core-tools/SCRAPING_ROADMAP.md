# UMD Faculty Scraping Roadmap

## Completed
- ✅ **A. James Clark School of Engineering** (185 faculty across 7 departments)
  - Engineering General: 24 faculty
  - Bioengineering: 24 faculty
  - Mechanical Engineering: 24 faculty
  - Electrical & Computer Engineering: 48 faculty
  - Civil & Environmental Engineering: 24 faculty
  - Aerospace Engineering: 23 faculty
  - Chemical & Biomolecular Engineering: 18 faculty
  - Database: `tools/clark_faculty.db`
  - Success rate: 99.5% with email (184/185), 75% with bio (139/185)

## Next Priority: CMNS (College of Computer, Mathematical, and Natural Sciences)

### Department URLs Found:
- **Computer Science**: https://www.cs.umd.edu/people/faculty
- **CMNS General**: https://cmns.umd.edu/people
- **Applied Mathematics & Statistics**: https://amsc.umd.edu/people/faculty/faculty-listing.html

### Additional CMNS departments to investigate:
- Mathematics
- Physics
- Chemistry
- Biology
- Astronomy
- Geology
- Atmospheric & Oceanic Science

## After CMNS: Robert H. Smith School of Business
- **URL**: https://www.rhsmith.umd.edu/directory
- Likely uses a different format than Clark School

## Later: Other Departments
- **College of Education**: https://education.umd.edu/faculty-directory
- **School of Public Health**: https://sph.umd.edu/people/faculty-staff
- **iSchool (College of Information Studies)**: Various research center pages
- **College of Arts and Humanities**: Need to investigate
- **Other schools and colleges**: TBD

## Notes
- Clark School departments all used the same `/clark/facultydir` CMS format, making scraping efficient
- Each college likely has its own CMS system and HTML structure
- Will need to investigate HTML structure for each new college before developing scrapers
