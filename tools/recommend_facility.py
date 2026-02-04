import subprocess
import json
import os
from pathlib import Path

# TOOL_SPEC = {
#     "name": "recommend_locations",
#     "description": "Suggests facilities or locations for recreational activities",
#     "parameters": ["fitness_goal", "location_or_housing", "transport"]
# }

from tools.tooling import Tool
from tools.tooling import tool

@tool
def recommend_facility(schedule=None, fitness_goal=None, location_or_housing=None, transport=None, topK=None):
    """
    Tool function for dynamic agent:
    Writes student preferences to recwell/input.json and runs the Node.js facility 
    matcher (facility_Matcher.js) to recommend recreational facilities based on 
    activity type, location, and scheduling preferences.

    Parameters:
    - schedule: list of class dicts (same format as recwell/input.json's "schedule")
        EXAMPLE SCHEDULE FOR REFERENCE:
        "schedule": [
        {
        "name": "Intro to CS",
        "start_time": "09:00",
        "end_time": "10:15",
        "days": "Mon/Wed/Fri",
        "location": "IRB Building"
        }
  ],
    - fitness_goal: string (e.g., "soccer", "weight training", "swimming")
        The type of activity or fitness objective the student wants to pursue
    - location_or_housing: string (e.g., "Montgomery Hall", "Ellicott Hall, 4052 Stadium Dr")
        Student's residence hall or current location on campus
    - transport: string ("walking", "biking", or "driving")
        Preferred method of transportation to the facility
    - topK: int (optional, default 5)
        Number of top facility recommendations to return

    Returns a dict with keys:
    - status: "success" or "error"
    - result: stdout from facility_Matcher.js (formatted recommendations)
    - parsed: JSON-parsed recommendations if available, otherwise None
    - stderr: any error messages from the Node script
    - returncode: subprocess exit code
    - path: file path of the written input.json
    """

    # Determine recwell folder relative to this script: ../recwell
    tools_dir = Path(__file__).resolve().parent
    project_root = tools_dir.parent
    recwell_dir = project_root / 'recwell'
    recwell_dir.mkdir(parents=True, exist_ok=True)

    input_path = recwell_dir / 'input.json'
    
    student_profile =  {
                "fitness_goal": fitness_goal,
                "location_or_housing": location_or_housing,
                "transport": transport,
                "duration_preference": 30,
                "time_preference": 'late'
            }
    
    payload = {
        "schedule": schedule,
        "student_profile": student_profile
    }


    # Write the input file (use standard input.json for facility_Matcher.js)
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    try:
        # Run facility_Matcher.js from the recwell folder
        result = subprocess.run(
            ['node', 'facility_Matcher.js'],
            cwd=str(recwell_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=120
        )

        status = 'success' if result.returncode == 0 else 'error'

        # Parse the stdout output (facility_Matcher prints formatted recommendations)
        parsed = None
        try:
            # Try to parse as JSON if it looks like JSON
            if result.stdout and result.stdout.strip().startswith('['):
                parsed = json.loads(result.stdout)
        except Exception:
            # If not JSON, just use the raw text
            parsed = result.stdout if result.stdout else None

        return {
            'result': result.stdout,
            'parsed': parsed,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'path': str(input_path),
            'status': status
        }

    except subprocess.TimeoutExpired as e:
        return {'status': 'error', 'error_message': 'timeout', 'path': str(input_path), 'stderr': str(e)}


if __name__ == '__main__':
    # Example quick run for dev: change values here as needed
    # Example: call with simple purpose (backwards-compatible)
    sample = recommend_facility(
        schedule=[
        {
            "name": "Calculus I",
            "start_time": "08:00",
            "end_time": "09:15",
            "days": "Tue/Thu",
            "location": "Math Building 204"
        },
        {
            "name": "General Chemistry",
            "start_time": "09:30",
            "end_time": "10:45",
            "days": "Mon/Wed/Fri",
            "location": "Science Hall 110"
        },
        {
            "name": "World History",
            "start_time": "11:00",
            "end_time": "12:15",
            "days": "Tue/Thu",
            "location": "Humanities Center 301"
        }],
        fitness_goal='Weight Training',
        location_or_housing='Ellicott Hall, 4052 Stadium Dr, College Park, MD 20742',
        transport='walking',
        topK=5
    )
    print(sample)

TOOL_SPEC = recommend_facility.tool_spec()