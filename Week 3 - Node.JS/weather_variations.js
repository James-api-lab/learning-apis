import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, ".env") });

const key = process.env.OPENWEATHER_API_KEY;
const cities = ["Seattle", "London", "Tokyo"];
const units = "imperial";

for (const city of cities) {
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(city)}&appid=${key}&units=${units}`;
  const res = await fetch(url);
  if (res.ok) {
    const data = await res.json();
    console.log(`${city}: ${data.main.temp}°C, Humidity ${data.main.humidity}%`);
  } else {
    console.log(`Error for ${city}:`, await res.text());
  }
}
