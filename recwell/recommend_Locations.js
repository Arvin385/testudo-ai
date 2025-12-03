import fs from 'fs';

// Lightweight dynamic fetch (matches project style in Implementationv1.js)
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

const FACILITIES_PATH = new URL('./facilities.json', import.meta.url).pathname;
const CACHE_PATH = new URL('./facilities_embeddings.json', import.meta.url).pathname;
const INPUT_PATH = new URL('./input.json', import.meta.url).pathname;

// Deterministic, non-AI recommender
// This implementation avoids external AI calls. It ranks facilities by matching
// user interest against facility types and keywords.

function tokenize(str) {
  return String(str || '')
    .toLowerCase()
    .split(/\W+/)
    .filter(t => t.length > 0);
}

/**
 * Calculate similarity between two strings (0-1).
 * Checks if tokens from userStr appear in facilityStr.
 */
function stringSimilarity(userStr, facilityStr) {
  const userTokens = tokenize(userStr);
  const facilityText = facilityStr.toLowerCase();
  
  if (userTokens.length === 0) return 0;
  
  let matches = 0;
  for (const token of userTokens) {
    if (facilityText.includes(token)) {
      matches += 1;
    }
  }
  return matches / userTokens.length;
}

function scoreFacilityByIntent(facility, userInterest) {
  let score = 0;
  
  // High weight: match against facility type
  const typeScore = stringSimilarity(userInterest, facility.type || '');
  score += typeScore * 3.0;
  
  // Medium weight: match against facility name
  const nameScore = stringSimilarity(userInterest, facility.name || '');
  score += nameScore * 2.0;
  
  // Low weight: match against location
  const locationScore = stringSimilarity(userInterest, facility.location || '');
  score += locationScore * 0.5;
  
  return score;
}

/**
 * Recommend locations based on a short user interest string.
 * Returns an array of {facility, score} sorted descending by score.
 */
export async function recommendLocations(userInterest, { apiKey = null, topK = 5 } = {}) {
  if (!userInterest || typeof userInterest !== 'string') throw new Error('userInterest must be a non-empty string');

  if (!fs.existsSync(FACILITIES_PATH)) return [];
  const facilitiesRaw = JSON.parse(fs.readFileSync(FACILITIES_PATH, 'utf-8'));
  const facilities = facilitiesRaw.Facilities || [];

  // Score each facility against the user interest
  const scored = facilities.map(f => {
    const score = scoreFacilityByIntent(f, userInterest);
    return { facility: f, score };
  });

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score);
  
  // Return top matches, or all if scores are zero
  const nonZero = scored.filter(s => s.score > 0);
  if (nonZero.length === 0) {
    // Fallback: return first topK facilities in order
    return scored.slice(0, Math.max(1, topK));
  }
  return nonZero.slice(0, topK);
}

export async function listFacilities() {
  if (!fs.existsSync(FACILITIES_PATH)) return [];
  const facilitiesRaw = JSON.parse(fs.readFileSync(FACILITIES_PATH, 'utf-8'));
  return facilitiesRaw.Facilities || [];
}

// Small helper to clear cache (useful for development)
export function clearEmbeddingsCache() {
  if (fs.existsSync(CACHE_PATH)) fs.unlinkSync(CACHE_PATH);
}

export default { recommendLocations, listFacilities, clearEmbeddingsCache };
