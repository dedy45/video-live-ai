import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import PerformerValidationPanel from '../components/panels/PerformerValidationPanel.svelte';

describe('PerformerValidationPanel', () => {
  it('renders validation actions for avatar, suara, and preview reachability', () => {
    render(PerformerValidationPanel, {
      props: {
        runningCheck: '',
        results: {},
        onRunCheck: vi.fn(),
      },
    });

    expect(screen.getByRole('button', { name: /cek kesiapan runtime/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cek engine avatar/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cek clone suara lokal/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cek chunking audio/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cek target preview/i })).toBeInTheDocument();
  });

  it('shows latest result and triggers the requested check', async () => {
    const onRunCheck = vi.fn();

    render(PerformerValidationPanel, {
      props: {
        runningCheck: '',
        results: {
          preview_targets: {
            label: 'Target Preview',
            status: 'fail',
            timestamp: '2026-03-11T03:10:00Z',
            summary: 'Preview vendor belum bisa dijangkau.',
          },
        },
        onRunCheck,
      },
    });

    expect(screen.getByText(/preview vendor belum bisa dijangkau/i)).toBeInTheDocument();
    await fireEvent.click(screen.getByRole('button', { name: /cek target preview/i }));
    expect(onRunCheck).toHaveBeenCalledWith('preview_targets');
  });
});
