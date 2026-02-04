import fs from 'fs';

import {Time} from './Time.js';

import {User} from './User.js';

import {Day} from './Day.js';

import {Workout} from './Workout.js';

import readline from 'readline';
import dotenv from 'dotenv';

// Load .env into process.env
dotenv.config();

/**
 * PART ONE - CREATE BASIC PLAN
 */

// Read the JSON file - data now holds all relevant data about the student and his/her schedule
const data = JSON.parse(fs.readFileSync('input.json', 'utf-8'));
// Create User object based on data from JSON
const user = new User(data.student_profile.experience_level, 
                      data.student_profile.fitness_goal, 
                      Number(data.student_profile.duration_preference), 
                      data.student_profile.time_preference);

// Function to convert schedule to 2D array of start and end times for each class
function scheduleToArray(schedule) {
  return schedule.map(cls => new Time(cls.start_time, cls.end_time));  
}


// Function to create array schedules for each day
function makeDailySchedules(classes) {
  // Create an array of classes for each day, stored in a Day object
  let days = [new Day("Mon", []), new Day("Tue", []), new Day("Wed", []), new Day("Thurs", []), new Day("Fri", [])];

  // Set up array of class times - use 6:00 AM and 12:00 AM as boundaries for earliest and latest
  // This is the hard-coded setting for Eppley timings(maybe adjust timings for user's preferred gym?)
  days.forEach(day => {
    day.schedule.push(new Time("6:00", "6:00"));
  })

  classes.forEach(cls => {
    if (cls.days.includes("Mon")) {
      days[0].schedule.push(new Time(cls.start_time, cls.end_time));
    }
    if (cls.days.includes("Tue")) {
      days[1].schedule.push(new Time(cls.start_time, cls.end_time));
    }
    if (cls.days.includes("Wed")) {
      days[2].schedule.push(new Time(cls.start_time, cls.end_time));
    }
    if (cls.days.includes("Thurs")) {
      days[3].schedule.push(new Time(cls.start_time, cls.end_time));
    }
    if (cls.days.includes("Fri")) {
      days[4].schedule.push(new Time(cls.start_time, cls.end_time));
    }
  })

  // This is the hard-coded setting for Eppley timings(maybe adjust timings for user's preferred gym?)
  days.forEach(day => {
    day.schedule.push(new Time("24:00", "24:00"));
  })

  return days;

}

// Before calling makeDailySchedules, check if schedule is empty. If it is, set daily_schedule to empty array
// Otherwise, parse the schedule array from JSON and then call makeDailySchedules
let daily_schedule;
// if (!Array.isArray(data.schedule) || data.schedule.length === 0) {
//   daily_schedule = [];
// } else {
  // Parse array from JSON
  let schedule = JSON.parse(data.schedule);
  daily_schedule = makeDailySchedules(schedule);
// }



// console.log(daily_schedule);

/* Example output for one day - each element has a two-element array with start and end time for one class:
[
  ["09:00", "10:15"],
  ["10:30", "11:45"],
  ["12:00", "13:15"],
  ["14:00", "15:15"],
  ["15:30", "16:45"]
]
*/

/**
 * Calculates the gap between two classes in minutes.
 * Adds a 30-minute buffer before the start and after the end of each class.
 * Returns -1 if the classes overlap or touch.
 *
 * @param {string} start1 - Start time of class 1 in "HH:MM" (24-hour)
 * @param {string} end1 - End time of class 1 in "HH:MM" (24-hour)
 * @param {string} start2 - Start time of class 2 in "HH:MM" (24-hour)
 * @param {string} end2 - End time of class 2 in "HH:MM" (24-hour)
 * @returns {number} Gap in minutes, or -1 if no gap
 */
function classGapInMinutes(class1, class2) {
  const toMinutes = (time) => {
    const [h, m] = time.split(":").map(Number);
    return h * 60 + m;
  };

  // Convert times to minutes
  let s1 = toMinutes(class1.start_time);
  let e1 = toMinutes(class1.end_time);
  let s2 = toMinutes(class2.start_time);
  let e2 = toMinutes(class2.end_time);

  // If buffer causes negative start, wrap around 0
  if (s1 < 0) s1 = 0;
  if (s2 < 0) s2 = 0;

  // Check for overlap: if intervals intersect
  if (!(e1 < s2 || e2 < s1)) return -1;

  // Compute gap between classes
  const gap = s2 > e1 ? s2 - e1 : s1 - e2;

  return gap;
}

/** 
 * For each gap in between classes - find adequate gaps, meaning the student has enough time in that
 * gap to get from where they are to the nearest facility using their preferred mode of transportation
 * 
 * Factor in preferred duration - do they have enough time to work out however long they want to? 
 * 
 * - We fill factor in exact transport time later by implementing Google Maps API 
 * */  
function adequateGaps(classList) {
    let gaps = [];
    for (let i = 0; i < classList.length - 1; i++) {
        if (classGapInMinutes(classList[i], classList[i+1]) - 30 >= user.duration_preference)
          gaps.push(new Time(classList[i].end_time, classList[i+1].start_time))
    }
    return gaps;
}

/** For each gap, find possible periods of time for working out; at the moment, I have taken 15 minutes
 *  from start and end - this should be adjusted from 15 to the actual transportation time(Google Maps API) */ 
function workoutTimes(gaps) {

  let workout_times = [];

  let preferred_duration = user.duration_preference;

  gaps.forEach(gap => {

    // Start and End for the entire gap(adjusted for travel - *Add travel time later(Google Maps API?))
    let adjusted_start = gap.minute_totals[0] + 15;
    let adjusted_end = gap.minute_totals[1] - 15;

    let current_minutes = adjusted_start;
    let new_start = 0;
    let new_end = 0;

    while (current_minutes <= adjusted_end - preferred_duration) {
      new_start = current_minutes;
      new_end = current_minutes + preferred_duration;
      let start_string = Time.minutesToTime(new_start);
      let end_string = Time.minutesToTime(new_end);
      workout_times.push(new Time(start_string, end_string));
      current_minutes = new_end;
    }

  }) 

  return workout_times;

}

// Preference is an "enum" variable - early, mid-day, or late(default early)
// For later use - to improve code readability, re-use, etc.
// const Preference = Object.freeze({
//   EARLY: "early",
//   MIDDAY: "mid-day",
//   LATE: "late"
// })

/** Consider time_preference(early, midday, or late) - filter out times that are not preferred by user */ 
function filter_suggestions(suggestions, preference) {
  
  // Filtered list to return
  let filtered_list = []; 

  // If preference is early, end at latest possible "early time"(before 11)
  // let max_early = 11*60;
  // If preference is mid-day, start at earliest possible/end at latest possible "mid-day time"(11 to 4)
  const START_MIDDAY = 11*60; // 11:00 AM converted to total minutes for easy comparison
  const END_MIDDAY = 16*60; // 4:00 PM converted to total minutes for easy comparison
  // If preference is late, start at earliest possible "late time"(after 4)
  // let min_late = 16*60;

  let min_minutes = 6*60;
  let max_minutes = 24*60;

  if (preference === "late") {
    min_minutes = END_MIDDAY;
  } else if (preference === "midday") {
    min_minutes = START_MIDDAY;
    max_minutes = END_MIDDAY;
  } else {
    max_minutes = START_MIDDAY;
  }

  suggestions.forEach(suggestion => {
    // [start, end] for suggested time block
    let minute_totals = suggestion.minute_totals;
    // If start is greater than minimum amount and less than maximum amount, include in filtered list
    if (minute_totals[0] > min_minutes && minute_totals[1] < max_minutes) {
      filtered_list.push(suggestion);
    }
  })

  return filtered_list;

}

/** Asynchronous because await is needed for while loop -> while user has not made choice and times
 * are still available in list, continue to toggle through solutions; finally either display selected 
 * time or indicate that there are no other suggestions
 */
function toggle_suggestions(filtered_suggestion_list) {
  // Non-interactive: choose the earliest (first) suggestion if available.
  if (!Array.isArray(filtered_suggestion_list) || filtered_suggestion_list.length === 0) return null;
  return filtered_suggestion_list[0];
}

// Call toggle function for the given suggestions of a particular day
function manage_toggle(day, suggestions) {
  // Non-interactive manager: automatically select earliest suggestion for the day
  const selected_time = toggle_suggestions(suggestions);
  if (selected_time) {
    return day.day + " " + Time.militaryToStandard(selected_time.start_time)
                           + " - " + Time.militaryToStandard(selected_time.end_time);
  }
  return day.day + " - No selection";
}

// Information regarding standard workout plan(what muscles to exercise when)
// const standard_plan_data = fs.readFileSync('plan.json', 'utf-8');
// let my_plan_data = JSON.parse(standard_plan_data);

let my_plan_data = new Workout(user.experience_level);

// Will later implement feature to customize plan based on user experience/goals

// Takes in workout_schedule(String Array) and plan_data(JSON data)
function add_plan_to_schedule(schedule, plan) {
  // Deterministic assignment: walk through plan.split/plan.schedule in order
  // without mutating the original plan object.
  const schedule_with_split = [];
  const split = Array.isArray(plan.split) ? plan.split.slice() : [];
  const exercises = Array.isArray(plan.schedule) ? plan.schedule.slice() : [];
  let idx = 0;

  schedule.forEach(daily_workout => {
    if (!daily_workout.includes("No selection") && split.length > 0 && exercises.length > 0) {
      const next_workout = split[idx % split.length];
      const next_exercises = exercises[idx % exercises.length];
      schedule_with_split.push(daily_workout + "\n" + next_workout + ":" + next_exercises);
      idx++;
    } else {
      schedule_with_split.push(daily_workout);
    }
  });

  return schedule_with_split;
}

// Create a workout_schedule(String Array) with suggested times for each day of the week
let workout_schedule = [];

// Non-interactive scheduler: pick earliest available time for each day automatically
function runScheduler() {
  for (const day of daily_schedule) {
    const gapList = adequateGaps(day.schedule);
    const possible_workout_times = workoutTimes(gapList);
    const filtered_suggestions = filter_suggestions(possible_workout_times, user.time_preference);

    const result = manage_toggle(day, filtered_suggestions); // manage_toggle now auto-selects earliest
    workout_schedule.push(result);
  }

  // Use helper method to add data for user-based workout split to schedule
  const workout_plan = add_plan_to_schedule(workout_schedule, my_plan_data);

  // Write newly created workout schedule to output text file
  const output = workout_plan.join("\n");
  // fs.writeFileSync("output.txt", output, "utf-8");

  return output;
}

// console.log(runScheduler());

// Create function that waits for runScheduler to finish, then uses the current_plan to generate a complete prompt(which is sent to Groq API)
// async function generatePlan() {
//   console.log(await runScheduler());
//   //return current_plan;
// }

let current_plan = runScheduler();

// console.log(await generatePlan());

// /**
//  * PART TWO - CUSTOMIZE PLAN
//  */

// // This portion needs to be asynchronous, waiting for runScheduler to finish

let context = 
  "You are a fitness trainer who is trying to help me reach my fitness goal: "
+ user.fitness_goal + ". I just want the schedule in my format. ";

let prompt = context + "Tailor the following workout plan for me without changing any of the start or end times"
+ "(while considering my fitness goal). "
+ "\n"
+ "After the entire schedule is printed, add a brief description of what you changed and how it helps me reach my goal.\n"
+ current_plan;

// Use API Key that connects to Groq API - Put in .env file and hide!

let groq_key = process.env.GROQ_API_KEY;

const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

async function queryGroq(prompt) {
  const API_KEY = groq_key; // Paste your Groq API key

  let custom_plan = "";

  try {
    
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_KEY}`
      },
      body: JSON.stringify({
        model: 'llama-3.1-8b-instant',  // Very fast model
        messages: [
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 1024
      })
    });
    
    if (!res.ok) {
      console.error('API Error:', res.status, await res.text());
      return;
    }
    
    const my_data = await res.json();
    
    custom_plan = my_data.choices[0].message.content;
    
    console.log(custom_plan);

    return custom_plan

  } catch (error) {

    return error.message;
    
  }
}

let customized_plan = await queryGroq(prompt);

fs.writeFileSync("output.txt", customized_plan, "utf-8");