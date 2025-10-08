import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

dotenv.config({ path: join(__dirname, ".env") });
const defaultUnits = (process.env.DEFAULT_UNITS === 'imperial') ? 'imperial' : 'metric';


const key = process.env.OPENWEATHER_API_KEY;
if (!key) {
  console.error("Missing OPENWEATHER_API_KEY");
  process.exit(1);
}

// define our CLI
const argv = yargs(hideBin(process.argv))
  .usage('$0 [options] <cities...>')
  .option('units', {
    type: 'string',
    choices: ['metric', 'imperial'],
    default: defaultUnits,
    describe: 'Units for temperature',
  })
  .demandCommand(1, 'Provide at least one city')
  .help()
  .parse();

const units = argv.units;           // "metric" or "imperial"
const unitSymbol = units === 'metric' ? 'C' : 'F';
const cities = argv._.map(String);  // city names from the CLI

for (const city of cities) {
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${key}&units=${units}`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error(`Error for ${city}:`, res.status, await res.text());
    continue;
  }
  const data = await res.json();
  console.log(`${city}: ${data.main.temp}°${unitSymbol}, Humidity ${data.main.humidity}%`);
}
