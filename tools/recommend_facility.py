import subprocess
import json
import os
from pathlib import Path

TOOL_SPEC = {
    "name": "recommend_locations",
    "description": "Writes a profile to recwell/ and runs the Node recommender to get facility recommendations (non-AI deterministic scorer).",
    "parameters": ["purpose", "location_or_housing", "transport", "duration_preference", "time_preference", "topK"]
}


def recommend_facility(payload=None, student_profile=None, purpose=None, location_or_housing="", transport="walking", duration_preference=45, time_preference="early", topK=5, api_key=None, input_filename='input_locations.json'):
    """
    Writes a payload (or builds one from the provided student_profile/purpose) to
    `recwell/<input_filename>` and runs the Node recommender `recommend_runner.js`.

    This matches the pattern used by `custom_workout_schedule.custom_workout_schedule`:
    - determines the `recwell` folder relative to this `tools` folder
    - writes the input file
    - runs the node script from `recwell/`

    Returns a dict containing: `result` (stdout), `stderr`, `returncode`, `path`, `status`.
    """

    # Determine recwell folder relative to this script: ../recwell
    tools_dir = Path(__file__).resolve().parent
    project_root = tools_dir.parent
    recwell_dir = project_root / 'recwell'
    recwell_dir.mkdir(parents=True, exist_ok=True)

    input_path = recwell_dir / input_filename

    # Build the body to write
    if payload and isinstance(payload, dict):
        to_write = payload
    elif student_profile and isinstance(student_profile, dict):
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

    # Prepare environment for subprocess. API key is optional for the new deterministic recommender.
    env = os.environ.copy()
    if api_key:
        env['OPENAI_API_KEY'] = api_key

    try:
        # Run node from the recwell folder and pass the absolute input path
        result = subprocess.run(
            ['node', 'recommend_runner.js', str(input_path), str(topK)],
            cwd=str(recwell_dir),
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=120
        )

        status = 'success' if result.returncode == 0 else 'error'

        # Try to parse the stdout as JSON (recommend_runner prints JSON results).
        parsed = None
        try:
            parsed = json.loads(result.stdout) if result.stdout else None
        except Exception:
            parsed = None

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
        purpose='Weight Training and Cardio',
        location_or_housing='Ellicott Hall, College Park, MD',
        transport='walking',
        duration_preference=45,
        time_preference='midday',
        topK=5
    )
    print(sample)
