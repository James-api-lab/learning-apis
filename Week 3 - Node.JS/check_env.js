import dotenv from "dotenv";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

// Recreate __dirname in ESM and load .env from THIS file's folder
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, ".env") });

const k = process.env.OPENWEATHER_API_KEY || "";
const masked = k ? `${k.slice(0, 4)}…(${k.length} chars)` : "(missing)";
console.log("OPENWEATHER_API_KEY:", masked);
