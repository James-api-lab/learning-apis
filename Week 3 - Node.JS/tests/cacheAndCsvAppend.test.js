import { describe, it, expect, beforeAll, afterAll } from '@jest/globals';
import { spawnSync } from 'child_process';
import { writeFileSync, mkdirSync, readFileSync, rmSync, existsSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = dirname(__dirname); // repo root

// helpers
const todayISO = new Date().toISOString().split('T')[0];
const cacheDir = join(projectRoot, 'cache');
const cacheFile = join(cacheDir, `${todayISO}.json`);
const csvPath = join(projectRoot, 'test-output.csv');

function runCli(args) {
  const res = spawnSync(process.execPath, ['weather_cli.js', ...args], {
    cwd: projectRoot,
    env: { ...process.env }, // no API key needed: we use --cache-day with a file
    encoding: 'utf8'
  });
  return res;
}

beforeAll(() => {
  // Ensure cache exists with known data (2 cities)
  mkdirSync(cacheDir, { recursive: true });
  const fake = [
    {
      city: "Seattle",
      ok: true,
      temp: 58.1,
      feels_like: 57.5,
      humidity: 84,
      weather: "light rain",
      wind_speed: 9.9,
      country: "US",
      obs_time_iso: "2025-10-01T00:00:00.000Z",
      units: "imperial"
    },
    {
      city: "Tokyo",
      ok: true,
      temp: 69.1,
      feels_like: 69.3,
      humidity: 76,
      weather: "moderate rain",
      wind_speed: 6.0,
      country: "JP",
      obs_time_iso: "2025-10-01T00:00:00.000Z",
      units: "imperial"
    }
  ];
  writeFileSync(cacheFile, JSON.stringify(fake, null, 2), 'utf8');
  // Clean old CSV if present
  if (existsSync(csvPath)) rmSync(csvPath);
});

afterAll(() => {
  // keep artifacts for debugging; uncomment to clean:
  // if (existsSync(csvPath)) rmSync(csvPath);
  // if (existsSync(cacheFile)) rmSync(cacheFile);
});

describe('cache + CSV append', () => {
  it('writes 2 rows on first run from cache (no header in append mode)', () => {
    const res = runCli(['Seattle', 'Tokyo', '--cache-day', '--csv-out', 'test-output.csv', '--quiet', '--json-only']);
    expect(res.status).toBe(0);
    const lines = readFileSync(csvPath, 'utf8').trim().split(/\r?\n/);
    // In append mode, csv-writer doesn't write a header for a new file.
    // We expect exactly 2 data rows (one per cached city).
    expect(lines.length).toBe(2);
  });

  it('appends 2 more rows on second run', () => {
    const res = runCli(['Seattle', 'Tokyo', '--cache-day', '--csv-out', 'test-output.csv', '--quiet', '--json-only']);
    expect(res.status).toBe(0);
    const lines = readFileSync(csvPath, 'utf8').trim().split(/\r?\n/);
    // Now we should have 4 data rows total.
    expect(lines.length).toBe(4);
  });
});
