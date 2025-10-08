import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, ".env") });

const key = process.env.OPENWEATHER_API_KEY;
if (!key) {
  console.error("Missing OPENWEATHER_API_KEY");
  process.exit(1);
}

// process.argv = ["node", "script.js", ...your args]
const cities = process.argv.slice(2);
if (cities.length === 0) {
  console.log('Usage: node weather_args_basic.js "Seattle" "Tokyo"');
  process.exit(0);
}

const units = "metric"; // fixed for now

for (const city of cities) {
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${key}&units=${units}`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error(`Error for ${city}:`, res.status, await res.text());
    continue;
    }
  const data = await res.json();
  console.log(`${city}: ${data.main.temp}°C, Humidity ${data.main.humidity}%`);
}
