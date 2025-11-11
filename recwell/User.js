export class User {
  constructor(experience_level, fitness_goal, location_or_housing, transport, duration_preference, time_preference) {
    const validExperience = ["beginner", "intermediate", "advanced"];
    //const validGoals = ["fun", "sports", "weight loss", "muscle gain"];
    const validTransport = ["driving", "transit", "walking", "cycling"];
    const validTimes = ["early", "midday", "late"];

    this.experience_level = validExperience.includes(experience_level.toLowerCase()) 
      ? experience_level 
      : "beginner";

    this.fitness_goal = fitness_goal; // should be left empty_string if none

    this.location_or_housing = location_or_housing || "Unknown";

    this.transport = validTransport.includes(transport.toLowerCase()) 
      ? transport 
      : "walking";

    this.duration_preference = (typeof duration_preference === "number" && duration_preference >= 30 && duration_preference <= 120)
      ? duration_preference 
      : 45;

    this.time_preference = validTimes.includes(time_preference.toLowerCase()) 
      ? time_preference 
      : "early";
  }
}