import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// Load .env next to this script
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, ".env") });

const key = process.env.OPENWEATHER_API_KEY;
if (!key) {
  console.error("Missing OPENWEATHER_API_KEY in .env");
  process.exit(1);
}

// Usage: node weather_one_city.js "Seattle" [metric|imperial]
const city = process.argv[2] || "Seattle";
const units = (process.argv[3] === "imperial") ? "imperial" : "metric";

const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${key}&units=${units}`;

try {
  const res = await fetch(url);
  if (!res.ok) {
    console.error("API error:", res.status, await res.text());
    process.exit(1);
  }
  const data = await res.json();
  const temp = data?.main?.temp;
  const hum = data?.main?.humidity;

  if (temp == null || hum == null) {
    console.error("Unexpected response shape:", JSON.stringify(data, null, 2));
    process.exit(1);
  }

  console.log(`${city}: ${temp}°${units === "metric" ? "C" : "F"}, Humidity ${hum}%`);
} catch (err) {
  console.error("Network or parsing error:", err.message);
  process.exit(1);
}
