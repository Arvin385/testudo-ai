export class Time {

  constructor(start_time, end_time) {
    this.start_time = start_time; // string "HH:MM"
    this.end_time = end_time;     // string "HH:MM"
    this.minute_totals = this.convertToMinutes(); // start and end Times in minutes
    this.duration = this.calculateDuration(); // duration in minutes
  }

  // Method to convert minutes to string for time
  static minutesToTime(total_minutes) {
    let hour = Math.floor(total_minutes / 60);
    let minutes = total_minutes % 60;

    return hour.toString().padStart(2, "0") + (":") + minutes.toString().padStart(2, "0");
  }

  // Method to convert any inputted time to minutes
  static timeToMinutes(time) {
    const [hour, min] = time.split(":").map(Number);
    return hour * 60 + min;
  }
  
  // Method to convert current time stored in this Time object to minutes
  // Return two-element array of minute conversions(for start and end times)
  convertToMinutes() {
    const startTotal = Time.timeToMinutes(this.start_time);
    const endTotal = Time.timeToMinutes(this.end_time);
    return [startTotal, endTotal];
  }

  // Method to calculate duration in minutes
  calculateDuration() {
    let start = this.minute_totals[0];
    let end = this.minute_totals[1];
    return end - start; // duration in minutes
  }

  static militaryToStandard(time_string) {
    let standard_time = "";
    const [hour, min] = time_string.split(":").map(Number);
    if (hour > 12) {
      let new_hour = hour-12;
      return new_hour.toString().padStart(2, "0") + (":") + min.toString().padStart(2, "0") + "PM";
    } else if (hour == 12) {
      return time_string + "PM";
    } else {
      return time_string + "AM";
    }
  }

}

