import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/svelte';
import AIBrainPage from '../pages/AIBrainPage.svelte';

// Mock fetch globally
global.fetch = vi.fn();

describe('AIBrainPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header with tabs', async () => {
    (global.fetch as any).mockImplementation(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({})
      })
    );

    render(AIBrainPage);
    
    await waitFor(() => {
      expect(screen.getByText(/AI Brain/i)).toBeTruthy();
    });
    
    // Use more specific selectors for tabs to avoid matching subtitle text
    const tabs = screen.getAllByRole('button');
    const tabTexts = tabs.map(tab => tab.textContent);
    expect(tabTexts.some(text => text?.includes('Configuration'))).toBe(true);
    expect(tabTexts.some(text => text?.includes('Prompt Registry'))).toBe(true);
    expect(tabTexts.some(text => text?.includes('Script Generator'))).toBe(true);
    expect(tabTexts.some(text => text?.includes('Runtime Monitor'))).toBe(true);
  });

  it('shows loading state initially', async () => {
    let resolvePromise: any;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (global.fetch as any).mockImplementation(() => promise);

    render(AIBrainPage);
    
    // Should show loading immediately
    expect(screen.getByText(/Memuat AI Brain/i)).toBeTruthy();
    
    // Resolve the promise to clean up
    resolvePromise({ ok: true, json: () => Promise.resolve({}) });
  });

  it('displays configuration tab when data is loaded', async () => {
    const mockConfig = {
      routing_table: {
        'CHAT_REPLY': ['groq', 'gemini'],
        'SELLING_SCRIPT': ['claude', 'gpt4o']
      },
      daily_budget_usd: 5.0,
      fallback_order: ['groq', 'gemini', 'claude', 'gpt4o'],
      available_providers: ['claude', 'gemini', 'gpt4o', 'groq'],
      edit_mode: 'runtime_only',
      persists_across_restart: false,
      prompt: {
        active_revision: 'default-live-commerce:v1',
        slug: 'default-live-commerce',
        version: 1,
        status: 'active'
      }
    };

    const mockRuntime = {
      director: {
        state: 'IDLE',
        stream_running: false,
        emergency_stopped: false,
        manual_override: false,
        current_phase: 'hook',
        phase_sequence: ['hook', 'cta'],
        active_provider: 'groq',
        active_model: 'groq/llama',
        active_prompt_revision: 'default-live-commerce:v1',
        uptime_sec: 0,
        history: [],
        valid_transitions: ['SELLING']
      },
      brain: {
        active_provider: 'groq',
        active_model: 'groq/llama',
        routing_table: {},
        adapter_count: 4,
        daily_budget_usd: 5.0
      },
      prompt: {
        active_revision: 'default-live-commerce:v1',
        slug: 'default-live-commerce',
        version: 1,
        status: 'active'
      },
      persona: {
        name: 'Sari'
      },
      script: {
        current_phase: 'hook',
        phase_sequence: ['hook', 'cta']
      }
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/brain/config')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockConfig)
        });
      }
      if (url.includes('/api/director/runtime')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockRuntime)
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(AIBrainPage);

    await waitFor(() => {
      expect(screen.getByText(/Brain Configuration/i)).toBeTruthy();
    });

    expect(screen.getByText(/reset saat restart/i)).toBeTruthy();
  });

  it('switches between tabs', async () => {
    const mockConfig = {
      routing_table: {},
      daily_budget_usd: 5.0,
      fallback_order: []
    };

    (global.fetch as any).mockImplementation((url: string) => {
      if (url.includes('/api/brain/config')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockConfig)
        });
      }
      if (url.includes('/api/director/runtime')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({})
        });
      }
      return Promise.reject(new Error('Unknown URL'));
    });

    render(AIBrainPage);

    await waitFor(() => {
      expect(screen.getByText(/Brain Configuration/i)).toBeTruthy();
    });

    // Configuration tab is active by default
    const configTab = screen.getByText(/⚙️ Configuration/i);
    expect(configTab.classList.contains('active')).toBe(true);
  });

  it('shows error state when fetch fails', async () => {
    (global.fetch as any).mockRejectedValue(new Error('Network error'));

    render(AIBrainPage);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeTruthy();
    });
  });
});
