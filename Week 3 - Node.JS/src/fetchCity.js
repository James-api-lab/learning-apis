// src/fetchCity.js
export async function fetchCity({ city, key, units }) {
  const url = `https://api.openweathermap.org/data/2.5/weather?q=${encodeURIComponent(
    city
  )}&appid=${key}&units=${units}`;

  try {
    const res = await fetch(url);

    if (!res.ok) {
      const raw = await res.text();
      let message = raw;
      try {
        const j = JSON.parse(raw);
        if (j && typeof j.message === 'string') message = j.message;
      } catch {}
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
      raw: data
    };
  } catch (err) {
    return { city, ok: false, error: err.message };
  }
}
