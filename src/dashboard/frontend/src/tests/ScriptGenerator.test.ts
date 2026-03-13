import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import ScriptGenerator from '../components/panels/ScriptGenerator.svelte';

describe('ScriptGenerator', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('posts the full script generation payload including provider and shows metadata', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        success: true,
        script: '1. HOOK: Halo kak!',
        provider: 'groq',
        model: 'groq/llama-3.3-70b-versatile',
        latency_ms: 12.5,
      }),
    });

    render(ScriptGenerator);

    await fireEvent.input(screen.getByLabelText(/product name/i), {
      target: { value: 'Lip Cream' },
    });
    await fireEvent.input(screen.getByLabelText(/price/i), {
      target: { value: '89000' },
    });
    await fireEvent.input(screen.getByLabelText(/features/i), {
      target: { value: 'matte\nringan' },
    });
    await fireEvent.change(screen.getByLabelText(/llm provider/i), {
      target: { value: 'groq' },
    });

    await fireEvent.click(screen.getByRole('button', { name: /generate script/i }));

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('/api/brain/generate-script');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body as string)).toMatchObject({
      product_name: 'Lip Cream',
      price: 89000,
      features: ['matte', 'ringan'],
      target_duration_sec: 30,
      provider: 'groq',
    });

    await screen.findByText(/1\. HOOK: Halo kak!/i);
    expect(
      screen.getByText((_, element) => element?.textContent?.trim() === 'Provider: groq')
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        (_, element) => element?.textContent?.trim() === 'Model: groq/llama-3.3-70b-versatile'
      )
    ).toBeInTheDocument();
    expect(screen.getByText(/12.5 ms/i)).toBeInTheDocument();
  });

  it('surfaces backend detail when script generation fails', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({
        detail: 'Prompt parse failed',
      }),
    });

    render(ScriptGenerator);

    await fireEvent.input(screen.getByLabelText(/product name/i), {
      target: { value: 'Lip Cream' },
    });
    await fireEvent.input(screen.getByLabelText(/price/i), {
      target: { value: '89000' },
    });
    await fireEvent.click(screen.getByRole('button', { name: /generate script/i }));

    expect(await screen.findByText(/prompt parse failed/i)).toBeInTheDocument();
  });
});
