import fs from 'fs';

/**
 * Automated Facility Matcher - Activity Type & Time Preference Only
 * Accepts preferences via command-line args or reads from input.json if available
 */

// Read facilities data
const facilitiesData = JSON.parse(fs.readFileSync('facilities.json', 'utf-8'));

/**
 * Parse input from command-line arguments or input.json
 * Command-line format: node facility_Matcher.js [fitnessGoal] [location] [timePreference] [maxResults]
 */
function parseInput() {
  const args = process.argv.slice(2);
  
  // Try to parse from command-line arguments first
  if (args.length > 0) {
    return {
      student_profile: {
        fitness_goal: args[0] || 'general fitness',
        location_or_housing: args[1] || '',
        time_preference: args[2] || 'early',
        max_facility_suggestions: parseInt(args[3]) || 3
      }
    };
  }
  
  // Fallback to input.json if no command-line args provided
  try {
    const inputData = JSON.parse(fs.readFileSync('input.json', 'utf-8'));
    return inputData;
  } catch (e) {
    // If no input.json, return defaults
    return {
      student_profile: {
        fitness_goal: 'general fitness',
        location_or_housing: '',
        time_preference: 'early',
        max_facility_suggestions: 3
      }
    };
  }
}

const inputData = parseInput();

/**
 * Normalizes a string for comparison
 */
function normalizeString(str) {
  return str.toLowerCase().trim().replace(/\s+/g, ' ');
}

/**
 * Maps fitness goals to facility types
 * Can handle both goal-based input (e.g., "Muscle gain") and direct facility types (e.g., "Swimming Pool")
 */
function getFacilityTypesForGoal(fitnessGoal) {
  const goalMapping = {
    'muscle gain': ['Weight Training', 'Personal Training'],
    'weight loss': ['Cardio', 'Swimming Pool', 'Personal Training'],
    'endurance': ['Cardio', 'Swimming Pool', 'Basketball Court'],
    'general fitness': ['Weight Training', 'Cardio', 'Swimming Pool'],
    'sports': ['Basketball Court', 'Tennis Courts', 'Club/Intramural Sports', 'Volleyball Court'],
    'flexibility': ['Cardio', 'Personal Training']
  };
  
  const normalizedGoal = normalizeString(fitnessGoal);
  
  // First, check if the input matches a mapped fitness goal
  for (const [goal, types] of Object.entries(goalMapping)) {
    if (normalizedGoal.includes(goal) || goal.includes(normalizedGoal)) {
      return types;
    }
  }
  
  // If no goal mapping found, check if input is a direct facility type
  // Get all unique facility types from facilities.json
  const allFacilityTypes = new Set();
  for (const facility of facilitiesData.Facilities) {
    const types = Array.isArray(facility.type) ? facility.type : [facility.type];
    types.forEach(type => allFacilityTypes.add(type));
  }
  
  // Check if user input matches any facility type directly
  for (const facilityType of allFacilityTypes) {
    const normalizedType = normalizeString(facilityType);
    if (normalizedGoal === normalizedType || 
        normalizedGoal.includes(normalizedType) || 
        normalizedType.includes(normalizedGoal)) {
      return [facilityType]; // Return as array for consistency
    }
  }
  
  // Default to general fitness facilities if nothing matches
  return ['Weight Training', 'Cardio'];
}

/**
 * Checks if facility is open during user's preferred time
 * Returns { isOpen: boolean, matchScore: number, reason: string }
 */
function checkTimeAvailability(facilityHours, userTimePreference) {
  // Handle 24 hour facilities
  if (facilityHours.includes('24 Hours') || facilityHours.includes('Open 24 Hours')) {
    return { 
      isOpen: true, 
      matchScore: 50, 
      reason: 'Open 24 hours (matches all time preferences)' 
    };
  }
  
  // Define time ranges for preferences
  const timeRanges = {
    'early': { description: 'early morning (6am-11am)' },
    'midday': { description: 'midday (11am-4pm)' },
    'late': { description: 'evening/late (4pm-12am)' }
  };
  
  const preferredRange = timeRanges[userTimePreference] || timeRanges['early'];
  
  // Check common patterns for late preference (most popular for students)
  if (userTimePreference === 'late') {
    // Facilities open until 12 am (midnight) are great for late preference
    if (facilityHours.includes('12 am') || facilityHours.includes('12:00 am')) {
      return {
        isOpen: true,
        matchScore: 40,
        reason: 'Open until midnight (perfect for late workouts)'
      };
    }
    // Facilities open until 10 pm are okay for late
    if (facilityHours.includes('10 pm')) {
      return {
        isOpen: true,
        matchScore: 30,
        reason: 'Open until 10pm (good for evening workouts)'
      };
    }
    // Facilities that close early (2pm, 4:30pm) are not ideal
    if (facilityHours.includes('2 pm') || facilityHours.includes('4:30 pm')) {
      return {
        isOpen: false,
        matchScore: -20,
        reason: 'Closes early (not ideal for late workouts)'
      };
    }
  }
  
  // Check for early preference
  if (userTimePreference === 'early') {
    // Facilities that open at 6 am are great for early birds
    if (facilityHours.includes('6 am')) {
      return {
        isOpen: true,
        matchScore: 40,
        reason: 'Opens at 6am (perfect for early morning)'
      };
    }
    // Facilities that open at 8 am are okay
    if (facilityHours.includes('8 am')) {
      return {
        isOpen: true,
        matchScore: 30,
        reason: 'Opens at 8am (good for morning workouts)'
      };
    }
  }
  
  // Check for midday preference
  if (userTimePreference === 'midday') {
    // Most facilities work for midday if they're open during standard hours
    if (facilityHours.includes('am') && facilityHours.includes('pm')) {
      return {
        isOpen: true,
        matchScore: 30,
        reason: 'Open during midday hours'
      };
    }
  }
  
  // Default: facility is probably open, but not optimized for preference
  return { 
    isOpen: true, 
    matchScore: 10, 
    reason: 'Check facility schedule for specific hours' 
  };
}

/**
 * Calculates match score between user preferences and facility
 */
function calculateMatchScore(facility, userPreferences) {
  let score = 0;
  let reasons = [];
  
  const fitnessGoal = userPreferences.fitness_goal || 'general fitness';
  const timePreference = userPreferences.time_preference || 'early';
  const userLocation = userPreferences.location_or_housing || '';
  
  // Get relevant facility types for the user's fitness goal
  const relevantTypes = getFacilityTypesForGoal(fitnessGoal);
  
  // Check if facility offers activities that match the fitness goal
  const facilityTypes = Array.isArray(facility.type) ? facility.type : [facility.type];
  
  let activityMatched = false;
  for (const type of facilityTypes) {
    for (const relevantType of relevantTypes) {
      const normalizedFacilityType = normalizeString(type);
      const normalizedRelevantType = normalizeString(relevantType);
      
      // Exact match
      if (normalizedFacilityType === normalizedRelevantType) {
        score += 100;
        reasons.push(`Has ${type} for ${fitnessGoal}`);
        activityMatched = true;
        break;
      }
      // Partial match
      else if (normalizedFacilityType.includes(normalizedRelevantType) || 
               normalizedRelevantType.includes(normalizedFacilityType)) {
        score += 60;
        reasons.push(`Has ${type} (supports ${fitnessGoal})`);
        activityMatched = true;
        break;
      }
    }
    if (activityMatched) break;
  }
  
  // If no activity match, check if it's a general fitness facility
  if (!activityMatched) {
    for (const type of facilityTypes) {
      const normalizedType = normalizeString(type);
      if (normalizedType.includes('weight') || normalizedType.includes('cardio') || 
          normalizedType.includes('gym')) {
        score += 30;
        reasons.push(`General fitness facility`);
        break;
      }
    }
  }
  
  // Check location match if user provided a location
  if (userLocation) {
    const normalizedUserLocation = normalizeString(userLocation);
    const facilityLocationText = normalizeString(`${facility.location} ${facility.address}`);
    
    if (facilityLocationText.includes(normalizedUserLocation) || 
        normalizeString('college park').includes(normalizedUserLocation) ||
        normalizedUserLocation.includes('college park')) {
      score += 50;
      reasons.push(`Near your location (${facility.location})`);
    }
  }
  
  // Check time availability
  const timeCheck = checkTimeAvailability(facility.hours, timePreference);
  score += timeCheck.matchScore;
  
  if (timeCheck.isOpen) {
    reasons.push(timeCheck.reason);
  } else {
    reasons.push(`⚠️ ${timeCheck.reason}`);
  }
  
  // Bonus for facilities with many activity types (versatile)
  if (Array.isArray(facility.type) && facility.type.length >= 5) {
    score += 15;
    reasons.push('Many activities available');
  }
  
  return { score, reasons };
}

/**
 * Finds best matching facilities
 */
function findBestFacilities(userPreferences, maxResults = 3) {
  const matches = [];
  
  for (const facility of facilitiesData.Facilities) {
    const matchResult = calculateMatchScore(facility, userPreferences);
    
    // Only include facilities with positive scores
    if (matchResult.score > 0) {
      matches.push({
        facility: facility,
        score: matchResult.score,
        reasons: matchResult.reasons
      });
    }
  }
  
  // Sort by score (descending)
  matches.sort((a, b) => b.score - a.score);
  
  // Return top N results
  return matches.slice(0, maxResults);
}

/**
 * Formats facility information for output
 */
function formatFacilityInfo(match, index) {
  const facility = match.facility;
  const types = Array.isArray(facility.type) ? facility.type.join(', ') : facility.type;
  
  return `
RECOMMENDATION #${index}
--------------------------------------------------
Facility: ${facility.name}
Location: ${facility.location}
Address: ${facility.address}
Activities Available: ${types}
Hours: ${facility.hours}
Match Score: ${match.score}/100
Why This Facility: ${match.reasons.join(' | ')}
--------------------------------------------------`;
}

/**
 * Main function - runs automatically like workout scheduler
 */
function runFacilityMatcher() {
  // Extract user preferences from parsed input (CLI args or input.json)
  const userPreferences = {
    fitness_goal: inputData.student_profile?.fitness_goal || 'general fitness',
    location_or_housing: inputData.student_profile?.location_or_housing || '',
    time_preference: inputData.student_profile?.time_preference || 'early',
    max_results: inputData.student_profile?.max_facility_suggestions || 3
  };
  
  // Build output header
  let output = `=== UMD FACILITY RECOMMENDATIONS ===\n\n`;
  output += `Based on your profile:\n`;
  output += `- Fitness Goal: ${userPreferences.fitness_goal}\n`;
  if (userPreferences.location_or_housing) {
    output += `- Location: ${userPreferences.location_or_housing}\n`;
  }
  output += `- Time Preference: ${userPreferences.time_preference}\n`;
  output += `- Requesting: Top ${userPreferences.max_results} facilities\n\n`;
  
  // Find matching facilities
  const results = findBestFacilities(userPreferences, userPreferences.max_results);
  
  if (results.length === 0) {
    output += '\nNo facilities found matching your criteria.\n';
    output += 'Try adjusting your fitness goal or time preference.\n';
  } else {
    output += `Found ${results.length} matching facilities:\n`;
    
    results.forEach((match, index) => {
      output += formatFacilityInfo(match, index + 1);
    });
    
    // Add summary section
    output += `\n\n=== SUMMARY ===\n`;
    output += `Best Match: ${results[0].facility.name}\n`;
    output += `Score: ${results[0].score}/100\n`;
    output += `Location: ${results[0].facility.location}\n`;
    output += `Address: ${results[0].facility.address}\n`;
    output += `Best For: ${userPreferences.fitness_goal}\n`;
    
    // Add quick comparison
    if (results.length > 1) {
      output += `\nAll Options:\n`;
      results.forEach((match, i) => {
        output += `  ${i + 1}. ${match.facility.name} (Score: ${match.score}/100)\n`;
      });
    }
  }
  
  // Write to output.txt
  fs.writeFileSync('output.txt', output, 'utf-8');
  
  console.log('Facility recommendations generated successfully!');
  console.log(`Results written to output.txt`);
  
  return output;
}

/**
 * Tailor a workout plan using the Groq API (Llama model).
 *
 * @param {Object} userProfile - object containing at least `fitness_goal` and other optional fields
 * @param {string} current_plan - the current workout schedule/plan as a single string
 * @param {Object} options - optional settings: { model, temperature, max_tokens, writeOutput }
 * @returns {Promise<string>} customized plan string
 */
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

export async function tailorPlan(userProfile, current_plan, options = {}) {
  const groq_key = process.env.GROQ_API_KEY;
  const model = options.model || 'llama-3.1-8b-instant';
  const temperature = typeof options.temperature === 'number' ? options.temperature : 0.7;
  const max_tokens = options.max_tokens || 1024;

  // Filter recommendations based on user's location
  let locationInfo = '';
  if (userProfile && userProfile.location_or_housing) {
    const userLocation = normalizeString(userProfile.location_or_housing);
    
    // Filter facilities by location match
    const locationFilteredFacilities = facilitiesData.Facilities.filter(f => {
      const facilityLocation = normalizeString(`${f.location} ${f.address}`);
      return facilityLocation.includes(userLocation) || userLocation.includes('college park');
    });
    
    if (locationFilteredFacilities.length > 0) {
      locationInfo = 
        `\nFiltered to facilities near: ${userProfile.location_or_housing}\n` +
        `Available facilities in your area: ${locationFilteredFacilities.map(f => f.name).join(', ')}\n`;
    }
  }

  const context =
    "You are a location recommender and information provider, helping me find the best facilities for my fitness goal and location and what those facilities have to offer: " +
    (userProfile && userProfile.fitness_goal ? userProfile.fitness_goal : '') +
    ". Location: " +
    (userProfile && userProfile.location_or_housing ? userProfile.location_or_housing : 'College Park, MD') +
    ". (Do not give me any extra information. I just want the top 3 facilities in my format)" +
    locationInfo + "\n";

  const prompt =
    "Tailor the following recommendations based on my fitness goal and location. " +
    "Prioritize facilities closest to: " +
    (userProfile && userProfile.location_or_housing ? userProfile.location_or_housing : 'College Park, MD') +
    ". " +
    "After the recommendations are printed, add a brief description of what other activities the facilities offer:\n" +
    current_plan;

  if (!groq_key) {
    throw new Error('GROQ_API_KEY not set in environment');
  }

  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${groq_key}`
      },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: context + prompt }],
        temperature,
        max_tokens
      })
    });

    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`API Error: ${res.status} ${txt}`);
    }

    const my_data = await res.json();
    const custom_plan = my_data?.choices?.[0]?.message?.content || '';

    if (options.writeOutput) {
      try {
        fs.writeFileSync('output.txt', custom_plan, 'utf-8');
      } catch (e) {
        // non-fatal; continue returning the plan
        console.warn('Warning: could not write output.txt', e.message);
      }
    }

    return custom_plan;
  } catch (err) {
    // bubble up a clear error message
    throw new Error(`tailorPlan error: ${err.message}`);
  }
}

// Run the matcher
const recommendations = runFacilityMatcher();
console.log('\n' + recommendations);