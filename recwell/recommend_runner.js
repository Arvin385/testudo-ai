import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { recommendLocations } from './recommend_Locations.js';

dotenv.config();

// Argument handling: allow either `node recommend_runner.js [topK]` (default behavior)
// or `node recommend_runner.js [inputPath] [topK]`. If an `input_locations.json` file
// exists it will be preferred over `input.json`.
const arg1 = process.argv[2];
let topK = 5;
// Correctly resolve script directory for both Windows and Unix
const scriptDir = path.dirname(decodeURIComponent(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1'));
let inputPath = path.join(scriptDir, 'input.json');
const altInputPath = path.join(scriptDir, 'input_locations.json');
if (fs.existsSync(altInputPath)) inputPath = altInputPath;

console.log(inputPath)

if (arg1) {
  const n = parseInt(arg1, 10);
  if (!Number.isNaN(n)) {
    topK = n;
  } else {
    // treat arg1 as input path
    inputPath = path.isAbsolute(arg1) ? arg1 : path.resolve(process.cwd(), arg1);
    const maybeTop = process.argv[3];
    if (maybeTop) {
      const n2 = parseInt(maybeTop, 10);
      if (!Number.isNaN(n2)) topK = n2;
    }
  }
}

function extractPurposeFromData(data) {
  if (!data) return null;
  // support multiple shapes: { profile: { purpose } } or { student_profile: { purpose|fitness_goal } }
  if (data.profile && data.profile.purpose) return String(data.profile.purpose).trim();
  if (data.student_profile) {
    if (data.student_profile.purpose) return String(data.student_profile.purpose).trim();
    if (data.student_profile.fitness_goal) return String(data.student_profile.fitness_goal).trim();
  }
  return null;
}

async function main() {
  try {
    if (!fs.existsSync(inputPath)) {
      console.error('ERROR: input file not found at', inputPath);
      process.exit(2);
    }

    const raw = fs.readFileSync(inputPath, 'utf-8');
    const data = JSON.parse(raw);
    const purpose = extractPurposeFromData(data);
    if (!purpose) {
      console.error('ERROR: could not determine purpose from input file');
      process.exit(3);
    }

    const results = await recommendLocations(purpose, { apiKey: process.env.OPENAI_API_KEY, topK });
    // Print JSON so calling tools can parse the output.
    console.log(JSON.stringify(results, null, 2));
  } catch (err) {
    console.error('ERROR', err.message || err);
    process.exit(1);
  }
}

main();
