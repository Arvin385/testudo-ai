export class User {
  constructor(experience_level, fitness_goal, duration_preference, time_preference) {
    const validExperience = ["beginner", "intermediate", "advanced"];
    const validTimes = ["early", "midday", "late"];

    this.experience_level = validExperience.includes(experience_level) 
      ? experience_level 
      : "beginner";

    this.fitness_goal = fitness_goal; // should be left empty_string if none

    this.duration_preference = (typeof duration_preference === "number" && duration_preference >= 30 && duration_preference <= 120)
      ? duration_preference 
      : 45;

    this.time_preference = validTimes.includes(time_preference) 
      ? time_preference 
      : "early";
  }
}