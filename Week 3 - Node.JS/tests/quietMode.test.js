import { describe, it, expect, beforeAll } from '@jest/globals';
import { spawnSync } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = dirname(__dirname);

const todayISO = new Date().toISOString().split('T')[0];
const cacheDir = join(projectRoot, 'cache');
const cacheFile = join(cacheDir, `${todayISO}.json`);

function runCli(args) {
  return spawnSync(process.execPath, ['weather_cli.js', ...args], {
    cwd: projectRoot,
    env: { ...process.env },
    encoding: 'utf8'
  });
}

beforeAll(() => {
  mkdirSync(cacheDir, { recursive: true });
  writeFileSync(
    cacheFile,
    JSON.stringify([{ city: "Paris", ok: true, temp: 62, feels_like: 60, humidity: 70, weather: "cloudy", wind_speed: 5, country: "FR", obs_time_iso: "2025-10-01T00:00:00.000Z", units: "imperial" }], null, 2),
    'utf8'
  );
});

describe('quiet mode', () => {
  it('produces no stdout when --quiet and --json-only (still works)', () => {
    const res = runCli(['"Paris"', '--cache-day', '--quiet', '--json-only']);
    expect(res.status).toBe(0);
    expect(res.stdout.trim()).toBe('');   // no human lines, no info logs
    // errors would still go to stderr, but there shouldn't be any
    expect(res.stderr.trim()).toBe('');
  });
});
