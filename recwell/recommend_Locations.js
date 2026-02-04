import fs from 'fs';

// Lightweight dynamic fetch (matches project style in Implementationv1.js)
const fetch = (...args) => import('node-fetch').then(({ default: fetch }) => fetch(...args));

const FACILITIES_PATH = new URL('./facilities.json', import.meta.url).pathname;
const CACHE_PATH = new URL('./facilities_embeddings.json', import.meta.url).pathname;
const INPUT_PATH = new URL('./input.json', import.meta.url).pathname;

// Choose an embeddings model. Adjust if you prefer a different model name.
const EMBEDDING_MODEL = 'text-embedding-3-small';

function cosineSimilarity(a, b) {
  let dot = 0.0;
  let normA = 0.0;
  let normB = 0.0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

async function embedText(apiKey, text) {
  if (!apiKey) throw new Error('OPENAI_API_KEY not set');

  const res = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({ model: EMBEDDING_MODEL, input: text })
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`OpenAI embeddings error: ${res.status} ${txt}`);
  }

  const data = await res.json();
  return data.data[0].embedding;
}

async function buildFacilityEmbeddings(apiKey) {
  if (!fs.existsSync(FACILITIES_PATH)) throw new Error('facilities.json not found');

  const facilitiesRaw = JSON.parse(fs.readFileSync(FACILITIES_PATH, 'utf-8'));
  const facilities = facilitiesRaw.Facilities || [];

  // If cache exists, return it
  if (fs.existsSync(CACHE_PATH)) {
    try {
      const cache = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
      // basic sanity check
      if (Array.isArray(cache) && cache.length === facilities.length) return cache;
    } catch (e) {
      // fallthrough to rebuild cache
    }
  }

  const results = [];

  for (const f of facilities) {
    const doc = `${f.name}. Type: ${f.type}. Location: ${f.location}. Address: ${f.address}. Hours: ${f.hours}`;
    const embedding = await embedText(apiKey, doc);
    results.push({ facility: f, embedding });
  }

  // Save cache (overwrite)
  try {
    fs.writeFileSync(CACHE_PATH, JSON.stringify(results), 'utf-8');
  } catch (e) {
    // non-fatal
    console.warn('Warning: could not write embeddings cache', e.message);
  }

  return results;
}

/**
 * Recommend locations based on a short user interest string.
 * Returns an array of {facility, score} sorted descending by score.
 */
export async function recommendLocations(userInterest, { apiKey = process.env.OPENAI_API_KEY, topK = 5 } = {}) {
  if (!userInterest || typeof userInterest !== 'string') throw new Error('userInterest must be a non-empty string');
  if (!apiKey) throw new Error('OPENAI_API_KEY must be provided either via options or environment');

  // Ensure facility embeddings are available (cached)
  const facilityEmbeddings = await buildFacilityEmbeddings(apiKey);

  // Embed user interest
  const userEmb = await embedText(apiKey, userInterest);

  // Score facilities
  const scored = facilityEmbeddings.map(item => {
    const score = cosineSimilarity(userEmb, item.embedding);
    return { facility: item.facility, score };
  });

  // Sort desc by score and return topK
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK);
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
