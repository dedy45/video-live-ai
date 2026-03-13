import { beforeEach, describe, expect, it, vi } from 'vitest';

const mountSpy = vi.fn(() => ({ destroy: vi.fn() }));

vi.mock('svelte', () => ({
  mount: mountSpy,
}));

vi.mock('../pages/AIBrainPage.svelte', () => ({
  default: { __test: 'AIBrainPageMock' },
}));

describe('aibrain standalone entry', () => {
  beforeEach(() => {
    vi.resetModules();
    mountSpy.mockClear();
    document.body.innerHTML = '<div id="app"></div>';
  });

  it('mounts the standalone AI Brain page with the Svelte 5 mount API', async () => {
    const module = await import('../entries/aibrain');

    expect(mountSpy).toHaveBeenCalledTimes(1);
    expect(mountSpy).toHaveBeenCalledWith(
      { __test: 'AIBrainPageMock' },
      { target: document.getElementById('app') }
    );
    expect(module.default).toBeDefined();
  });
});
