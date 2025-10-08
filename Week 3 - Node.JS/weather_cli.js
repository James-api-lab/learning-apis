/*
BIG PICTURE — weather_cli.js

1) Imports & setup
2) Config & flags
3) Helpers (tsName, hintForError)
4) Fetch function
5) Cache handling
6) Output (human, JSON/CSV, auto/daily, chart)
7) Run log
*/

// #region 1) Imports & setup
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';
import { createObjectCsvWriter } from 'csv-writer';
import { existsSync, readFileSync, writeFileSync, mkdirSync, appendFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '.env'), quiet: true });
// #endregion

// #region 2) Config & flags
const key = process.env.OPENWEATHER_API_KEY;
if (!key) {
  console.error('Missing OPENWEATHER_API_KEY in .env');
  process.exit(1);
}

const defaultUnits =
  (process.env.DEFAULT_UNITS === 'imperial' || process.env.DEFAULT_UNITS === 'metric')
    ? process.env.DEFAULT_UNITS
    : 'imperial';

const argv = yargs(hideBin(process.argv))
  .usage('Usage: $0 [options] <cities...>\n\nExample:\n  $0 --units imperial "Seattle" "Dallas" --csv-out out.csv')
  .option('units', {
    type: 'string',
    choices: ['metric', 'imperial'],
    default: defaultUnits,
    describe: 'Units for temperature',
  })
  .option('json', {
    type: 'boolean',
    default: false,
    describe: 'Also print a JSON array of results',
  })
  .option('json-only', {
    type: 'boolean',
    default: false,
    describe: 'Suppress human lines; only emit JSON/CSV if requested',
  })
  .option('json-out', {
    type: 'string',
    describe: 'Write full JSON results to a file (e.g., weather.json)',
  })
  .option('csv-out', {
    type: 'string',
    describe: 'Append results to CSV (e.g., weather.csv)',
  })
  .option('csv-daily', {
    type: 'boolean',
    default: false,
    describe: 'Append results to weather-YYYY-MM-DD.csv (auto daily file)',
  })
  .option('csv-auto', {
    type: 'boolean',
    default: false,
    describe: 'Append CSV rows to a timestamped file (auto filename)',
  })
  .option('json-auto', {
    type: 'boolean',
    default: false,
    describe: 'Write JSON to a timestamped file (auto filename)',
  })
  .option('chart-out', {
    type: 'string',
    describe: 'Write a chart PNG of this run\'s temps (e.g., weather.png)',
  })
  .option('chart-type', {
    type: 'string',
    choices: ['bar', 'line'],
    default: 'bar',
    describe: 'Type of chart to generate (bar or line)',
  })
  .option('chart-from-csv', {
    type: 'string',
    describe: 'Generate chart from existing CSV file instead of current run',
  })
  .option('cache-day', {
    type: 'boolean',
    default: false,
    describe: 'Cache results in cache/YYYY-MM-DD.json and reuse them for the same day',
  })
  .option('summary', {
    type: 'boolean',
    default: false,
    describe: 'Print a one-line summary at the end (OK vs errors)',
  })
  .option('quiet', {
    type: 'boolean',
    default: false,
    describe: 'Suppress non-error console output (still writes JSON/CSV/logs)',
  })
  .demandCommand(0) // Don't require any commands by default
  .check((argv) => {
    // Only require cities if not using --chart-from-csv
    if (!argv['chart-from-csv'] && argv._.length === 0) {
      throw new Error('Provide at least one city (unless using --chart-from-csv)');
    }
    return true;
  })
  .help()
  .parse();

const units = argv.units;
const unitSymbol = units === 'imperial' ? 'F' : 'C';
const windUnit = units === 'metric' ? 'm/s' : 'mph';
const cities = argv._.map(String);
// #endregion

// #region 3) Helpers
function tsName(prefix, ext) {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const stamp =
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}_` +
    `${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}`;
  return `${prefix}-${stamp}.${ext}`;
}

function hintForError(status, errorText = '') {
  const t = String(errorText).toLowerCase();

  if (status === 401 || t.includes('invalid api key')) {
    return 'Hint: Your API key looks invalid. Check OPENWEATHER_API_KEY in .env (and that dotenv loads from this folder).';
  }
  if (status === 404 || t.includes('city not found') || t.includes('not found')) {
    return 'Hint: City not found — check spelling. If it has spaces, put it in quotes (e.g., "New York").';
  }
  if (status === 429 || t.includes('too many') || t.includes('rate')) {
    return 'Hint: Rate limited by OpenWeather — wait a minute or reduce requests (use --cache-day).';
  }
  if (status === 400 && (t.includes('nothing to geocode') || t.includes('bad request'))) {
    return 'Hint: Empty or invalid city. Provide at least one valid city name.';
  }
  if (status >= 500) {
    return 'Hint: OpenWeather server issue. Try again shortly.';
  }
  return null;
}
// #endregion

// #region 4) Fetch function
/**
 * @param {string} city
 * @returns {Promise<{ok:boolean, city:string, temp:number|null, feels_like:number|null, humidity:number|null, weather:string|null, wind_speed:number|null, country:string|null, obs_time_unix:number|null, obs_time_iso:string|null, units:string, raw?:any, status?:number, error?:string}>}
 */
async function fetchCity(city) {
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(
    city
  )}&appid=${key}&units=${units}`;

  try {
    const res = await fetch(url);

    // Improved error capture: try to parse OpenWeather's JSON "message"
    if (!res.ok) {
      const raw = await res.text();
      let message = raw;
      try {
        const j = JSON.parse(raw);
        if (j && typeof j.message === 'string') message = j.message;
      } catch { /* not JSON */ }
      return { city, ok: false, status: res.status, error: message };
    }

    const data = await res.json();
    const dt = data?.dt ?? null;
    return {
      city,
      ok: true,
      temp: data?.main?.temp ?? null,
      feels_like: data?.main?.feels_like ?? null,
      humidity: data?.main?.humidity ?? null,
      weather: data?.weather?.[0]?.description ?? null,
      wind_speed: data?.wind?.speed ?? null,
      country: data?.sys?.country ?? null,
      obs_time_unix: dt,
      obs_time_iso: dt ? new Date(dt * 1000).toISOString() : null,
      units,
      raw: data,
    };
  } catch (err) {
    return { city, ok: false, error: err.message };
  }
}
// #endregion

// #region 5) Cache handling
const todayISO = new Date().toISOString().split('T')[0];
const cacheDir = join(__dirname, 'cache');
const cacheFile = join(cacheDir, `${todayISO}.json`);

let results = [];
let source = 'live';

// Skip fetching if only generating chart from CSV
if (argv['chart-from-csv'] && !argv['csv-out'] && !argv['csv-daily'] && !argv['csv-auto'] && !argv['json-out'] && !argv['json-auto']) {
  // Only generating chart from CSV, no need to fetch data
  if (!argv.quiet) console.log('Skipping weather fetch (only generating chart from CSV)');
} else if (cities && cities.length > 0) {
  // Try to read cache if requested and file exists
  if (argv['cache-day'] && existsSync(cacheFile)) {
    try {
      results = JSON.parse(readFileSync(cacheFile, 'utf8'));
      if (!argv.quiet) console.log(`Using cached results from ${cacheFile}`);
      source = 'cache';
    } catch (e) {
      if (!argv.quiet) console.warn('Cache unreadable, fetching fresh:', e.message);
      results = await Promise.all(cities.map(fetchCity));
      mkdirSync(cacheDir, { recursive: true });
      writeFileSync(cacheFile, JSON.stringify(results, null, 2), 'utf8');
      if (!argv.quiet) console.log(`Cached results written to ${cacheFile}`);
    }
  } else {
    // No cache or not requested → fetch fresh
    results = await Promise.all(cities.map(fetchCity));
    if (argv['cache-day']) {
      mkdirSync(cacheDir, { recursive: true });
      writeFileSync(cacheFile, JSON.stringify(results, null, 2), 'utf8');
      if (!argv.quiet) console.log(`Cached results written to ${cacheFile}`);
    }
  }
}
// #endregion

// helper to resolve CSV destination based on flags
function resolveCsvPath() {
  if (argv['csv-out']) {
    return join(process.cwd(), argv['csv-out']); // explicit file
  }
  if (argv['csv-daily']) {
    return join(process.cwd(), `weather-${todayISO}.csv`); // daily file
  }
  if (argv['csv-auto']) {
    return join(process.cwd(), tsName('weather', 'csv')); // timestamped file
  }
  return null;
}

// #region 6) Output
let jsonOutRecorded = '';
let csvOutRecorded  = '';

// human-readable lines (unless --json-only or --quiet)
if (!argv['json-only'] && !argv.quiet) {
  for (const r of results) {
    if (!r.ok) {
      console.error(`Error for ${r.city}: ${r.status ?? ''} ${r.error ?? ''}`);
      const hint = hintForError(r.status, r.error);
      if (hint) console.error(hint);
      continue;
    }
    console.log(
      `${r.city}${r.country ? ', ' + r.country : ''}: ` +
      `${r.temp}°${unitSymbol} (feels ${r.feels_like}°${unitSymbol}), ` +
      `Humidity ${r.humidity}%, Wind ${r.wind_speed} ${windUnit} — ` +
      `${r.weather} — ${r.obs_time_iso ?? ''}`
    );
  }
}

// JSON to console (optional)
if (argv.json) {
  console.log(JSON.stringify(results, null, 2));
}

// JSON to file (optional)
if (argv['json-out']) {
  const outPath = join(process.cwd(), argv['json-out']);
  writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf8');
  jsonOutRecorded = argv['json-out'];
  if (!argv.quiet) console.log(`JSON written: ${argv['json-out']}`);
}

// JSON auto filename
if (argv['json-auto']) {
  const name = tsName('weather', 'json');
  const outPath = join(process.cwd(), name);
  writeFileSync(outPath, JSON.stringify(results, null, 2), 'utf8');
  jsonOutRecorded = name;
  if (!argv.quiet) console.log(`JSON written: ${name}`);
}

// CSV to file (append mode) — supports csv-out, csv-daily, csv-auto
const chosenCsvPath = resolveCsvPath();
if (chosenCsvPath) {
  const csvWriter = createObjectCsvWriter({
    path: chosenCsvPath,
    header: [
      { id: 'city', title: 'City' },
      { id: 'country', title: 'Country' },
      { id: 'temp', title: 'Temp' },
      { id: 'feels_like', title: 'FeelsLike' },
      { id: 'humidity', title: 'Humidity' },
      { id: 'weather', title: 'Weather' },
      { id: 'wind_speed', title: 'WindSpeed' },
      { id: 'obs_time_iso', title: 'ObsTimeISO' },
      { id: 'units', title: 'Units' },
      { id: 'ok', title: 'OK' },
      { id: 'status', title: 'Status' },
      { id: 'error', title: 'Error' }
    ],
    append: true
  });

  const rows = results.map((r) => ({
    city: r.city,
    country: r.ok ? r.country : null,
    temp: r.ok ? r.temp : null,
    feels_like: r.ok ? r.feels_like : null,
    humidity: r.ok ? r.humidity : null,
    weather: r.ok ? r.weather : null,
    wind_speed: r.ok ? r.wind_speed : null,
    obs_time_iso: r.ok ? r.obs_time_iso : null,
    units: r.units ?? units,
    ok: r.ok,
    status: r.status ?? '',
    error: r.ok ? '' : r.error ?? '',
  }));

  await csvWriter.writeRecords(rows);
  csvOutRecorded = chosenCsvPath.split(/[/\\]/).pop(); // filename only
  if (!argv.quiet) console.log(`CSV written: ${csvOutRecorded}`);
}

// Chart generation - either from CSV or from current run
if (argv['chart-out']) {
  try {
    // Dynamic import for QuickChart
    const { default: QuickChart } = await import('quickchart-js');
    
    let chartData = [];
    let chartTitle = '';
    
    if (argv['chart-from-csv']) {
      // Read data from CSV file
      const csvPath = join(process.cwd(), argv['chart-from-csv']);
      
      if (!existsSync(csvPath)) {
        console.error(`CSV file not found: ${argv['chart-from-csv']}`);
      } else {
        console.log(`Reading data from ${argv['chart-from-csv']}...`);
        const { parse } = await import('csv-parse/sync');
        const csvContent = readFileSync(csvPath, 'utf8');
        
        const records = parse(csvContent, {
          columns: true,
          skip_empty_lines: true
        });
        
        // Debug: show first record to understand the structure
        if (records.length > 0 && !argv.quiet) {
          console.log('Sample record:', records[0]);
        }
        
        // Filter valid records and prepare data
        chartData = records
          .filter(r => (r.OK === 'true' || r.OK === true) && r.Temp && r.Temp !== 'null' && r.Temp !== '')
          .map(r => ({
            city: r.City,
            temp: parseFloat(r.Temp),
            humidity: r.Humidity ? parseFloat(r.Humidity) : null,
            time: r.ObsTimeISO || new Date().toISOString()
          }));
          
        chartTitle = `Historical Weather Data from ${argv['chart-from-csv']}`;
        console.log(`Found ${chartData.length} valid records in CSV`);
      }
    } else {
      // Use current run data
      const okResults = results.filter(r => r.ok);
      chartData = okResults.map(r => ({
        city: r.city,
        temp: r.temp,
        humidity: r.humidity,
        time: r.obs_time_iso || new Date().toISOString()
      }));
      chartTitle = `Weather Conditions — ${new Date().toISOString()}`;
    }
    
    // Skip chart if no valid data
    if (chartData.length === 0) {
      console.warn('No valid weather data to chart');
    } else {
      const myChart = new QuickChart();
      
      // For CSV data, create a proper time series
      if (argv['chart-from-csv']) {
        if (argv['chart-type'] === 'line') {
          // Group data by city for line chart - each city gets its own line
          const cityGroups = {};
          chartData.forEach(d => {
            if (!cityGroups[d.city]) {
              cityGroups[d.city] = [];
            }
            cityGroups[d.city].push({
              time: new Date(d.time),
              temp: d.temp
            });
          });
          
          // Sort each city's data by time
          Object.keys(cityGroups).forEach(city => {
            cityGroups[city].sort((a, b) => a.time - b.time);
          });
          
          // Get all unique timestamps and sort them
          const allTimes = [...new Set(chartData.map(d => d.time))].sort();
          
          // Create labels from timestamps
          const labels = allTimes.map(t => {
            const date = new Date(t);
            return date.toLocaleString('en-US', { 
              month: 'short', 
              day: 'numeric', 
              hour: '2-digit', 
              minute: '2-digit' 
            });
          });
          
          // Define colors for different cities
          const colors = [
            'rgb(255, 99, 132)',   // Red
            'rgb(54, 162, 235)',   // Blue
            'rgb(255, 206, 86)',   // Yellow
            'rgb(75, 192, 192)',   // Teal
            'rgb(153, 102, 255)',  // Purple
            'rgb(255, 159, 64)',   // Orange
          ];
          
          // Create a dataset for each city
          const datasets = [];
          let colorIndex = 0;
          
          Object.keys(cityGroups).forEach(city => {
            const cityData = cityGroups[city];
            
            // Map city's temperatures to all timestamps (null if no data for that time)
            const temperatures = allTimes.map(time => {
              const dataPoint = cityData.find(d => d.time.toISOString() === time);
              return dataPoint ? dataPoint.temp : null;
            });
            
            datasets.push({
              label: city,
              data: temperatures,
              borderColor: colors[colorIndex % colors.length],
              backgroundColor: 'transparent',
              borderWidth: 2,
              fill: false,
              spanGaps: true, // Connect points even if there are nulls in between
              lineTension: 0.1 // Slight curve for smoother lines
            });
            
            colorIndex++;
          });
          
          // Create the line chart configuration
          myChart.setConfig({
            type: 'line',
            data: {
              labels: labels,
              datasets: datasets
            },
            options: {
              title: {
                display: true,
                text: `Weather Temperature Trends Over Time`
              },
              legend: {
                display: true,
                position: 'top'
              },
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: false
                  },
                  scaleLabel: {
                    display: true,
                    labelString: `Temperature (°${unitSymbol})`
                  }
                }],
                xAxes: [{
                  scaleLabel: {
                    display: true,
                    labelString: 'Date/Time'
                  },
                  ticks: {
                    maxRotation: 45,
                    minRotation: 45
                  }
                }]
              }
            }
          });
          
          // Log summary of what was plotted
          if (!argv.quiet && cityGroups && Object.keys(cityGroups).length > 0) {
            console.log(`\nChart Summary:`);
            console.log(`  Cities plotted: ${Object.keys(cityGroups).join(', ')}`);
            console.log(`  Time range: ${new Date(allTimes[0]).toLocaleString()} to ${new Date(allTimes[allTimes.length - 1]).toLocaleString()}`);
            console.log(`  Total data points: ${chartData.length}`);
            Object.keys(cityGroups).forEach(city => {
              const temps = cityGroups[city].map(d => d.temp);
              const avg = temps.reduce((a, b) => a + b, 0) / temps.length;
              const min = Math.min(...temps);
              const max = Math.max(...temps);
              console.log(`  ${city}: ${temps.length} measurements, ${min.toFixed(1)}°-${max.toFixed(1)}°${unitSymbol} (avg: ${avg.toFixed(1)}°)`);
            });
          }
        } else {
          // Bar chart - show all data points
          const labels = chartData.map((d, i) => `${d.city} (${i + 1})`);
          const tempData = chartData.map(d => d.temp);
          
          myChart.setConfig({
            type: 'bar',
            data: {
              labels: labels,
              datasets: [{
                label: `Temperature (°${unitSymbol})`,
                data: tempData,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
              }]
            },
            options: {
              title: {
                display: true,
                text: chartTitle
              },
              legend: {
                display: false
              },
              scales: {
                yAxes: [{
                  ticks: {
                    beginAtZero: false
                  },
                  scaleLabel: {
                    display: true,
                    labelString: `Temperature (°${unitSymbol})`
                  }
                }],
                xAxes: [{
                  scaleLabel: {
                    display: true,
                    labelString: 'Measurements'
                  }
                }]
              }
            }
          });
        }
      } else {
        // Current run data (existing logic)
        const labels = chartData.map(d => d.city);
        const tempData = chartData.map(d => d.temp);
        const humidityData = chartData.map(d => d.humidity);
        
        if (argv['chart-type'] === 'line') {
          // LINE CHART configuration - simplified for QuickChart
          myChart.setConfig({
            type: 'line',
            data: {
              labels: labels,
              datasets: [
                {
                  label: `Temperature (°${unitSymbol})`,
                  data: tempData,
                  borderColor: 'rgb(255, 99, 132)',
                  backgroundColor: 'rgba(255, 99, 132, 0.1)',
                  borderWidth: 2,
                  fill: false
                },
                {
                  label: 'Humidity (%)',
                  data: humidityData,
                  borderColor: 'rgb(54, 162, 235)',
                  backgroundColor: 'rgba(54, 162, 235, 0.1)',
                  borderWidth: 2,
                  fill: false
                }
              ]
            },
            options: {
              title: {
                display: true,
                text: chartTitle
              },
              legend: { 
                display: true
              },
              scales: { 
                yAxes: [{
                  ticks: {
                    beginAtZero: false
                  },
                  scaleLabel: {
                    display: true,
                    labelString: `Temperature (°${unitSymbol}) / Humidity (%)`
                  }
                }],
                xAxes: [{
                  scaleLabel: {
                    display: true,
                    labelString: 'Cities'
                  }
                }]
              }
            }
          });
        } else {
          // BAR CHART configuration (default) - simplified for QuickChart
          myChart.setConfig({
            type: 'bar',
            data: {
              labels: labels,
              datasets: [{
                label: `Temperature (°${unitSymbol})`,
                data: tempData,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
              }]
            },
            options: {
              title: {
                display: true,
                text: chartTitle
              },
              legend: { 
                display: false 
              },
              scales: { 
                yAxes: [{
                  ticks: {
                    beginAtZero: false
                  },
                  scaleLabel: {
                    display: true,
                    labelString: `Temperature (°${unitSymbol})`
                  }
                }],
                xAxes: [{
                  scaleLabel: {
                    display: true,
                    labelString: 'Cities'
                  }
                }]
              }
            }
          });
        }
      }
      
      // Set dimensions
      myChart.setWidth(argv['chart-from-csv'] ? 1200 : 900);
      myChart.setHeight(argv['chart-from-csv'] ? 600 : 500);
      myChart.setBackgroundColor('white');
      
      // Generate the chart as a binary buffer
      const imageBuffer = await myChart.toBinary();
      
      // Write to file
      const outPath = join(process.cwd(), argv['chart-out']);
      writeFileSync(outPath, imageBuffer);
      
      const chartType = argv['chart-type'] === 'line' ? 'Line' : 'Bar';
      const source = argv['chart-from-csv'] ? ` from ${argv['chart-from-csv']}` : '';
      if (!argv.quiet) console.log(`${chartType} chart written: ${argv['chart-out']}${source}`);
    }
  } catch (chartError) {
    console.error('Chart generation failed:', chartError.message);
    console.error('Continuing with other outputs...');
  }
}

// Summary line
if (argv.summary && !argv.quiet && !argv['json-only']) {
  const okCount = results.filter(r => r.ok).length;
  const errCount = results.length - okCount;
  console.log(`Summary: ${okCount} OK, ${errCount} errors`);
}
// #endregion

// #region 7) Run log
try {
  const logsDir = join(__dirname, 'logs');
  mkdirSync(logsDir, { recursive: true });

  const logPath = join(logsDir, 'weather_runs.csv');
  const nowIso = new Date().toISOString();

  const successCount = results.filter(r => r.ok).length;
  const errorCount = results.length - successCount;

  const citiesJoined = cities.join(';');
  const jsonOut = jsonOutRecorded ? String(jsonOutRecorded) : '';
  const csvOut  = csvOutRecorded  ? String(csvOutRecorded)  : '';

  if (!existsSync(logPath)) {
    writeFileSync(
      logPath,
      'timestamp,units,source,cities,success_count,error_count,json_out,csv_out\n',
      'utf8'
    );
  }

  const row = [
    nowIso,
    units,
    source,
    `"${citiesJoined.replace(/"/g, '""')}"`,
    successCount,
    errorCount,
    `"${jsonOut.replace(/"/g, '""')}"`,
    `"${csvOut.replace(/"/g, '""')}"`,
  ].join(',') + '\n';

  appendFileSync(logPath, row, 'utf8');
} catch (e) {
  console.warn('Run log append failed:', e.message);
}
// #endregion