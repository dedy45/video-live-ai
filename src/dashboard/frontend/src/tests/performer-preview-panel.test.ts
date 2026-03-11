import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import PerformerPreviewPanel from '../components/panels/PerformerPreviewPanel.svelte';

describe('PerformerPreviewPanel', () => {
  it('shows fallback guidance when preview targets are unreachable', async () => {
    const refreshTargets = vi.fn();

    render(PerformerPreviewPanel, {
      props: {
        loading: false,
        checkedAt: '2026-03-11T03:06:00Z',
        targets: {
          webrtcapi: {
            url: 'http://localhost:8010/webrtcapi.html',
            reachable: false,
            http_status: null,
            error: 'Connection refused',
          },
          dashboard_vendor: {
            url: 'http://localhost:8010/dashboard.html',
            reachable: false,
            http_status: null,
            error: 'Connection refused',
          },
          rtcpushapi: {
            url: 'http://localhost:8010/rtcpushapi.html',
            reachable: false,
            http_status: null,
            error: 'Connection refused',
          },
        },
        onRefresh: refreshTargets,
      },
    });

    expect(screen.getByText(/preview belum bisa dibuka/i)).toBeInTheDocument();
    expect(screen.getByText(/connection refused/i)).toBeInTheDocument();
    expect(screen.queryByTitle(/preview avatar/i)).not.toBeInTheDocument();

    await fireEvent.click(screen.getByRole('button', { name: /cek lagi/i }));
    expect(refreshTargets).toHaveBeenCalledTimes(1);
  });

  it('renders embedded preview when target is reachable', () => {
    render(PerformerPreviewPanel, {
      props: {
        loading: false,
        checkedAt: '2026-03-11T03:06:00Z',
        targets: {
          webrtcapi: {
            url: 'http://localhost:8010/webrtcapi.html',
            reachable: true,
            http_status: 200,
            error: null,
          },
          dashboard_vendor: {
            url: 'http://localhost:8010/dashboard.html',
            reachable: true,
            http_status: 200,
            error: null,
          },
          rtcpushapi: {
            url: 'http://localhost:8010/rtcpushapi.html',
            reachable: true,
            http_status: 200,
            error: null,
          },
        },
        onRefresh: vi.fn(),
      },
    });

    const frame = screen.getByTitle(/preview avatar/i);
    expect(frame).toHaveAttribute('src', 'http://localhost:8010/webrtcapi.html');
    expect(screen.queryByText(/preview belum bisa dibuka/i)).not.toBeInTheDocument();
  });
});
