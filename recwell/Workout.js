// Workout.js
export class Workout {
  constructor(experienceLevel = "beginner") {
    this.experienceLevel = experienceLevel.toLowerCase();
    this.setPlan();
  }

  setPlan() {
    switch (this.experienceLevel) {
      // INTERMEDIATE PLAN (1 rest day with light movement)
      case "intermediate":
        this.frequency = 5;
        this.split = ["Upper", "Lower", "Push", "Rest", "Pull"];
        this.schedule = [
          ["Bench Press", "Pull-Ups", "Overhead Press", "Barbell Row", "Face Pulls"],
          ["Back Squats", "Romanian Deadlifts", "Walking Lunges", "Leg Curls", "Standing Calf Raises"],
          ["Incline Dumbbell Press", "Overhead Shoulder Press", "Lateral Raises", "Tricep Dips", "Push-Ups"],
          [
            "Light Jog or 20-Minute Walk",
            "Dynamic Stretching (Leg Swings, Arm Circles)",
            "Foam Rolling (Full Body)",
            "Yoga Flow (10-15 min)",
            "Core Activation (Planks or Dead Bugs)" 
          ],
          ["Deadlifts", "Seated Cable Row", "Lat Pulldown", "Bicep Curls", "Hammer Curls"]
        ];
        break;

      // ADVANCED PLAN (0 rest days)
      case "advanced":
        this.frequency = 5;
        this.split = ["Push", "Pull", "Legs", "Upper Power", "Lower Power"];
        this.schedule = [
          ["Barbell Bench Press (Heavy)", "Overhead Barbell Press", "Incline Dumbbell Press", "Lateral Raises (High Rep)", "Skull Crushers"],
          ["Weighted Pull-Ups", "Pendlay Rows", "Chest Supported Rows", "Reverse Flys", "Barbell Curls"],
          ["Back Squats (Heavy)", "Front Squats", "Romanian Deadlifts", "Walking Lunges", "Standing Calf Raises"],
          ["Flat Bench Press", "Weighted Pull-Ups", "Overhead Press", "Barbell Rows", "Close-Grip Bench Press"],
          ["Deadlifts (Heavy)", "Paused Squats", "Deficit Lunges", "Leg Extensions", "Seated Calf Raises"]
        ];
        break;

      // BEGINNER PLAN (2 rest days with light stretching)
      default:
        this.frequency = 5;
        this.split = ["Full Body A", "Rest", "Full Body B", "Rest", "Full Body C"];
        this.schedule = [
          ["Bodyweight Squats", "Push-Ups (or Knee Push-Ups)", "Seated Cable Row", "Dumbbell Shoulder Press", "Plank (3x30s)"],
          [
            "10–15 Minute Walk",
            "Gentle Stretching (Hamstrings, Chest, Shoulders)",
            "Foam Rolling (Quads and Back)",
            "Deep Breathing Exercises",
            "Mobility Flow (Cat-Cow, Hip Circles)"
          ],
          ["Leg Press", "Incline Dumbbell Press", "Lat Pulldowns", "Lateral Raises", "Bicep Curls"],
          [
            "Light Yoga Session (10 min)",
            "Ankle and Shoulder Mobility Drills",
            "Stretch Band Work",
            "Short Walk or Bike Ride",
            "Neck and Upper Back Release"
          ],
          ["Goblet Squats", "Bench Press (Light)", "Assisted Pull-Ups", "Overhead Press", "Hanging Knee Raises"]
        ];
        break;
    }
  }

}