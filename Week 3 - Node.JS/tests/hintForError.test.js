import { describe, it, expect } from '@jest/globals';
import { hintForError } from '../src/hintForError.js';

describe('hintForError', () => {
  it('suggests checking API key on 401', () => {
    expect(hintForError(401, 'invalid api key')).toMatch(/api key/i);
  });

  it('suggests checking city spelling on 404', () => {
    expect(hintForError(404, 'city not found')).toMatch(/city not found/i);
  });

  it('suggests waiting on 429', () => {
    expect(hintForError(429, 'Too Many Requests')).toMatch(/rate/i);
  });

  it('returns null for other statuses', () => {
    expect(hintForError(418, 'I am a teapot')).toBeNull();
  });
});
