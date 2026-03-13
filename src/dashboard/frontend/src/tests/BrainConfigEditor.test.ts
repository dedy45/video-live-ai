import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import BrainConfigEditor from '../components/panels/BrainConfigEditor.svelte';

describe('BrainConfigEditor', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('saves runtime-only config edits through the AI Brain endpoint', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        status: 'updated',
      }),
    });

    const onUpdate = vi.fn();

    render(BrainConfigEditor, {
      props: {
        config: {
          daily_budget_usd: 5,
          fallback_order: ['groq', 'gemini'],
          routing_table: {
            chat_reply: ['groq', 'gemini'],
          },
          available_providers: ['gemini', 'groq'],
          edit_mode: 'runtime_only',
          persists_across_restart: false,
        },
        onUpdate,
      },
    });

    await fireEvent.click(screen.getByRole('button', { name: /edit configuration/i }));
    await fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/brain/config');
    expect(options.method).toBe('PUT');
    expect(JSON.parse(options.body as string)).toMatchObject({
      daily_budget_usd: 5,
      fallback_order: ['groq', 'gemini'],
      routing_table: {
        chat_reply: ['groq', 'gemini'],
      },
    });

    vi.advanceTimersByTime(500);
    await waitFor(() => {
      expect(onUpdate).toHaveBeenCalledTimes(1);
    });
  });

  it('shows API save failures to the operator', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({
        detail: 'unknown providers: legacy',
      }),
    });

    render(BrainConfigEditor, {
      props: {
        config: {
          daily_budget_usd: 5,
          fallback_order: ['groq', 'gemini'],
          routing_table: {
            chat_reply: ['groq', 'gemini'],
          },
          available_providers: ['gemini', 'groq'],
          edit_mode: 'runtime_only',
          persists_across_restart: false,
        },
      },
    });

    await fireEvent.click(screen.getByRole('button', { name: /edit configuration/i }));
    await fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    expect(await screen.findByText(/failed to save configuration/i)).toBeInTheDocument();
  });
});
