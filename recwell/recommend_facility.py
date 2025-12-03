import subprocess
import json
import os
from pathlib import Path

TOOL_SPEC = {
    "name": "recommend_locations",
    "description": "Takes an input file (schedule) containing a simple profile (purpose, location, transport, preferences) and runs the Node recommender to get facility recommendations.",
    "parameters": ["purpose", "location_or_housing", "transport", "duration_preference", "time_preference", "topK", "api_key"]
}


def recommend_facility(payload=None, student_profile=None, purpose=None, location_or_housing="", transport="walking", duration_preference=45, time_preference="early", topK=5, api_key=None, input_filename='input_locations.json'):
    """
    Accepts either a full `payload` dict, a `student_profile` dict (similar to `recwell/input.json`),
    or a purpose string (backwards-compatible). Writes the chosen payload to `recwell/<input_filename>`
    and runs `node recwell/recommend_runner.js` to produce recommendations.
    """

    project_root = Path(__file__).resolve().parent.parent
    recwell_dir = project_root / 'recwell'
    recwell_dir.mkdir(parents=True, exist_ok=True)

    input_path = recwell_dir / input_filename

    # Determine what to write
    if payload and isinstance(payload, dict):
        to_write = payload
    elif student_profile and isinstance(student_profile, dict):
        # normalize student_profile keys with sensible defaults
        sp = {}
        sp['experience_level'] = student_profile.get('experience_level', student_profile.get('experience', 'beginner'))
        sp['fitness_goal'] = student_profile.get('fitness_goal', student_profile.get('goal', ''))
        sp['location_or_housing'] = student_profile.get('location_or_housing', student_profile.get('location', ''))
        sp['transport'] = student_profile.get('transport', 'walking')
        sp['duration_preference'] = student_profile.get('duration_preference', student_profile.get('duration', duration_preference))
        sp['time_preference'] = student_profile.get('time_preference', student_profile.get('time', time_preference))

        to_write = {
            "student_profile": sp,
            "schedule": []
        }
    else:
        # backwards-compatible minimal payload based on purpose
        if not purpose:
            raise ValueError('Either payload (dict), student_profile (dict), or purpose (string) must be provided')
        to_write = {
            "profile": {
                "purpose": purpose,
                "location_or_housing": location_or_housing,
                "transport": transport,
                "duration_preference": duration_preference,
                "time_preference": time_preference
            }
        }

    # Write the input file
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(to_write, f, indent=2)

    # Prepare environment for subprocess
    env = os.environ.copy()
    if api_key:
        env['OPENAI_API_KEY'] = api_key

    try:
        result = subprocess.run(
            ['node', 'recommend_runner.js', str(topK)],
            cwd=str(recwell_dir),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=120
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "path": str(input_path)
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "error_message": "timeout", "path": str(input_path)}


if __name__ == '__main__':
    # Example quick run for dev: change values here as needed
    # Example: call with simple purpose (backwards-compatible)
    sample = recommend_facility(
        purpose='yoga and group fitness',
        location_or_housing='College Park, MD',
        transport='walking',
        duration_preference=45,
        time_preference='midday',
        topK=5
    )
    print(sample)
