import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import PromptEditorPanel from '../components/panels/PromptEditorPanel.svelte';

describe('PromptEditorPanel', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('exposes accessible persona controls including catchphrases and forbidden topics', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    render(PromptEditorPanel);

    vi.advanceTimersByTime(120);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/brain/prompts');
    });

    await fireEvent.click(screen.getByRole('button', { name: /create new revision/i }));

    expect(screen.getByLabelText(/^slug$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^name$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/personality/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/tone/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/expertise/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/catchphrases/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/forbidden topics/i)).toBeInTheDocument();
  });

  it('stores catchphrases and forbidden topics as arrays when saving a draft', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 2, status: 'draft' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

    render(PromptEditorPanel);

    vi.advanceTimersByTime(120);
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/brain/prompts');
    });

    await fireEvent.click(screen.getByRole('button', { name: /create new revision/i }));
    await fireEvent.input(screen.getByLabelText(/catchphrases/i), {
      target: { value: 'Halo kak\nCheckout sekarang' },
    });
    await fireEvent.input(screen.getByLabelText(/forbidden topics/i), {
      target: { value: 'politik\nagama' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /^save$/i }));

    const [, options] = fetchMock.mock.calls[1];
    expect(JSON.parse(options.body as string)).toMatchObject({
      persona: {
        catchphrases: ['Halo kak', 'Checkout sekarang'],
        forbidden_topics: ['politik', 'agama'],
      },
    });
  });
});
