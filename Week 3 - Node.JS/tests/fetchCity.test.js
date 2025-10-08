import { describe, it, expect, jest } from '@jest/globals';
import { fetchCity } from '../src/fetchCity.js';

describe('fetchCity', () => {
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
    expect(r.temp).toBe(20);
    expect(r.country).toBe('US');
    expect(typeof r.obs_time_iso).toBe('string');
  });

  it('returns ok=false with status/message on error (mocked 404)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: async () => JSON.stringify({ message: 'city not found' })
    });

    const r = await fetchCity({ city: 'Seattlle', key: 'TEST', units: 'metric' });
    expect(r.ok).toBe(false);
    expect(r.status).toBe(404);
    expect(String(r.error).toLowerCase()).toContain('city not found');
  });
});
