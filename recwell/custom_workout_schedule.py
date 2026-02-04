import subprocess
import json

# TOOL_SPEC = {
#     "name": "custom_workout_schedule",
#     "description": "Creates a customized workout schedule based on user class schedule(UMD Courses), time preference, duration preference, fitness goal, experience level",
#     "parameters": ["schedule", "time_preference", "duration_preference", "fitness_goal", "experience_level"] # names of required parameters 
# }

from tools.tooling import Tool
from tools.tooling import tool

@tool
def custom_workout_schedule(schedule, time_preference, duration_preference, fitness_goal, experience_level):
    """
    Tool function for dynamic agent:
    Overwrites recwell/input.json with the provided UMD class schedule and a student_profile built
    from the function parameters, then runs the Node scheduler located in the recwell
    folder (Implementationv1.js).

    Parameters
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
    - time_preference: string ("early", "midday", or "late")
    - duration_preference: int (minutes)
    - fitness_goal: string
    - experience_level: string ("beginner", "intermediate", "advanced")

    Returns a dict with keys: returncode, stdout, stderr, and path (written input.json path).
    """

    from pathlib import Path

    # Determine recwell folder relative to this script: ../recwell
    tools_dir = Path(__file__).resolve().parent
    project_root = tools_dir.parent
    recwell_dir = project_root / 'recwell'
    recwell_dir.mkdir(parents=True, exist_ok=True)
    input_path = recwell_dir / 'input.json'

    # Build student_profile object; fill in missing fields with empty strings
    student_profile = {
        "experience_level": experience_level,
        "fitness_goal": fitness_goal,
        "duration_preference": duration_preference,
        "time_preference": time_preference
    }

    payload = {
        "schedule": schedule,
        "student_profile": student_profile
    }

    # Write the file (overwrite)
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    # Run the node script from the recwell folder
    try:
        result = subprocess.run(
            ['node', 'Implementationv1.js'],
            cwd=str(recwell_dir),
            capture_output=True,
            text=True,
            check=False,
            timeout=120
        )

        return {"result": result.stdout, "status": "success"}

    except subprocess.TimeoutExpired as e:
        return {"status": "error", "error_message": result.stderr}
    

if __name__ == '__main__':
    
    # Example call and output

    schedule = [
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
    },
    {
        "name": "Intro to Computer Science",
        "start_time": "13:00",
        "end_time": "14:15",
        "days": "Mon/Wed/Fri",
        "location": "IRB Building 102"
    },
    {
        "name": "English Composition",
        "start_time": "15:00",
        "end_time": "16:15",
        "days": "Mon/Wed",
        "location": "Liberal Arts 215"
    }
    ]

    result = custom_workout_schedule([], "late", 60, "Basketball", "Intermediate")
    print(result)

TOOL_SPEC = custom_workout_schedule.tool_spec()
