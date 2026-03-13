import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import DirectorRuntimePanel from '../components/panels/DirectorRuntimePanel.svelte';

describe('DirectorRuntimePanel', () => {
  it('renders nested director runtime contract fields', () => {
    render(DirectorRuntimePanel, {
      props: {
        runtime: {
          director: {
            state: 'SELLING',
            stream_running: true,
            emergency_stopped: false,
            manual_override: false,
            current_phase: 'hook',
            phase_sequence: ['hook', 'cta'],
            active_provider: 'groq',
            active_model: 'groq/llama-3.3-70b-versatile',
            active_prompt_revision: 'launch:v2',
            uptime_sec: 42,
            history: [],
            valid_transitions: ['REACTING', 'ENGAGING'],
          },
          brain: {
            active_provider: 'groq',
            active_model: 'groq/llama-3.3-70b-versatile',
            routing_table: {
              chat_reply: ['groq', 'gemini'],
            },
            adapter_count: 2,
            daily_budget_usd: 7.5,
          },
          prompt: {
            active_revision: 'launch:v2',
            slug: 'launch',
            version: 2,
            status: 'active',
          },
          persona: {
            name: 'Sari',
            tone: 'warm',
          },
          script: {
            current_phase: 'hook',
            phase_sequence: ['hook', 'cta'],
          },
        },
      },
    });

    expect(screen.getByRole('heading', { name: /current state/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /active provider/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /active prompt/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /current phase/i })).toBeInTheDocument();
    expect(screen.getByText('SELLING')).toBeInTheDocument();
    expect(screen.getByText('groq')).toBeInTheDocument();
    expect(screen.getByText('launch:v2')).toBeInTheDocument();
    expect(screen.getByText('hook')).toBeInTheDocument();
  });
});
