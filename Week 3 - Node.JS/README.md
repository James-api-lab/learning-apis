 command-line tool to fetch live weather data using the OpenWeather API.  
Supports multiple cities, configurable units, JSON/CSV export, daily caching, run logging, and basic error hints.

---

## Setup

1) Install dependencies:
```bash
pnpm install
```

2) Create `.env` in the project folder:
```ini
OPENWEATHER_API_KEY=your_key_here
DEFAULT_UNITS=imperial
```
> `DEFAULT_UNITS` accepts `imperial` or `metric`.

---

## Usage

**Basic:**
```bash
node weather_cli.js "Seattle" "Tokyo"
```

**Change units:**
```bash
node weather_cli.js --units metric "Seattle"
```

**Use daily cache (reuses results for the same date):**
```bash
node weather_cli.js --cache-day "Seattle" "Tokyo"
```

**Export JSON + CSV (CSV appends new rows each run):**
```bash
node weather_cli.js --json-only --json-out weather.json --csv-out weather.csv "Seattle" "Tokyo"
```

**Quiet mode (suppress non-error logs):**
```bash
node weather_cli.js --quiet "Seattle" "Tokyo"
```

---

## Features

- 🌍 Fetch live weather from OpenWeather for multiple cities
- ⚙️ CLI flags:
  - `--units` (`metric`/`imperial`)
  - `--json` (print JSON to console)
  - `--json-only` (suppress human-readable lines)
  - `--json-out <file>` (save JSON)
  - `--csv-out <file>` (append CSV rows)
  - `--cache-day` (cache results in `cache/YYYY-MM-DD.json`)
  - `--quiet` (suppress non-error console output)
- 🧾 Logs:
  - `logs/weather_runs.csv` — timestamp, cities, success/error counts, and output files
- 🛟 Error hints for common API issues (401/404/429, etc.)

---

## Error Handling

The CLI returns structured errors per city and prints a human hint. Examples:

- `401 Unauthorized` — likely missing or invalid API key  
- `404 Not Found` — city name is invalid (check spelling, quote names with spaces)  
- `429 Too Many Requests` — API rate limit exceeded

Each city result looks like:
```json
{
  "city": "Atlantis",
  "ok": false,
  "status": 404,
  "error": "city not found"
}
```

---

## ✅ Testing

This project uses **Jest** (ESM mode) with mocked `fetch` to unit-test the core modules.

### What’s covered
- `src/fetchCity.js` — success/error shaping for API calls
- `src/hintForError.js` — maps status/text to human-friendly hints

### Project setup for tests
- ESM is enabled via `"type": "module"` in `package.json`.
- Jest runs in ESM mode using Node’s VM Modules.

Relevant `package.json` bits:
```json
{
  "type": "module",
  "scripts": {
    "test": "node --experimental-vm-modules ./node_modules/jest/bin/jest.js"
  },
  "devDependencies": {
    "@jest/globals": "^29.7.0",
    "jest": "^29.7.0"
  },
  "jest": {
    "testEnvironment": "node"
  }
}
```

### Run tests
```bash
pnpm test
# or
npm test
```

### Test files
```
tests/
  fetchCity.test.js      # mocks global.fetch; ok=true and ok=false paths
  hintForError.test.js   # pure function tests for error-to-hint mapping
```

Example (from `fetchCity.test.js`):
```js
import { describe, it, expect, jest } from '@jest/globals';
import { fetchCity } from '../src/fetchCity.js';

it('returns ok=true on success (mocked)', async () => {
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      dt: 1700000000,
      main: { temp: 20, feels_like: 19, humidity: 50 },
      weather: [{ description: 'clear sky' }],
      wind: { speed: 3 },
      sys: { country: 'US' }
    })
  });

  const r = await fetchCity({ city: 'Seattle', key: 'TEST', units: 'metric' });
  expect(r.ok).toBe(true);
  expect(r.city).toBe('Seattle');
});
```

### Common issues & fixes
- **“Cannot use import statement outside a module”**  
  Ensure:
  - `package.json` has `"type": "module"`.
  - Test script uses `node --experimental-vm-modules …`.
  - Tests use `import` + `@jest/globals` (not `require`).

- **“does not provide an export named 'fetchCity'”**  
  Confirm a **named export** in `src/fetchCity.js`:
  ```js
  export async function fetchCity(...) { ... }
  ```

- **“Your test suite must contain at least one test”**  
  Add at least one `it(...)` and check for syntax errors at the top of the file.

---

## Repo Structure (simplified)

```
.
├─ weather_cli.js
├─ src/
│  ├─ fetchCity.js
│  └─ hintForError.js
├─ tests/
│  ├─ fetchCity.test.js
│  └─ hintForError.test.js
├─ cache/
├─ logs/
│  └─ weather_runs.csv
├─ .env
└─ README.md
```
