// @vitest-environment node

import { describe, it, expect } from 'vitest';
import config from '../../vite.config';

describe('Vite multipage build config', () => {
  it('registers standalone operator pages as build inputs', () => {
    const inputs = config.build?.rollupOptions?.input as Record<string, string> | undefined;

    expect(inputs).toBeTruthy();
    expect(Object.keys(inputs ?? {})).toEqual(
      expect.arrayContaining([
        'index',
        'setup',
        'performer',
        'monitor',
        'stream',
        'products',
      ]),
    );
    expect(Object.keys(inputs ?? {})).not.toContain('validation');
    expect(Object.keys(inputs ?? {})).not.toContain('diagnostics');
  });
});
