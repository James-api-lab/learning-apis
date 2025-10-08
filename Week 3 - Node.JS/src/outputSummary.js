export function hintForError(status, errorText = '') {
    const t = String(errorText).toLowerCase();
  
    if (status === 401 || t.includes('invalid api key')) {
      return 'Hint: Your API key looks invalid. Check OPENWEATHER_API_KEY in .env.';
    }
    if (status === 404 || t.includes('city not found') || t.includes('not found')) {
      return 'Hint: City not found — check spelling (quote names with spaces).';
    }
    if (status === 429 || t.includes('too many') || t.includes('rate')) {
      return 'Hint: Rate limited — wait a bit or use --cache-day.';
    }
    if (status === 400 && (t.includes('nothing to geocode') || t.includes('bad request'))) {
      return 'Hint: Empty or invalid city name.';
    }
    if (status >= 500) {
      return 'Hint: OpenWeather server issue. Try again shortly.';
    }
    return null;
  }
  