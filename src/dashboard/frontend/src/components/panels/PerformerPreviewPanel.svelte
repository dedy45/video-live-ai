<script lang="ts">
  import type { LiveTalkingDebugTargets } from '../../lib/types';

  interface Props {
    loading: boolean;
    checkedAt: string | null;
    targets: LiveTalkingDebugTargets['targets'] | null;
    onRefresh: () => void | Promise<void>;
  }

  let { loading, checkedAt, targets, onRefresh }: Props = $props();

  const previewTarget = $derived(targets?.webrtcapi ?? null);
  const previewReady = $derived(Boolean(previewTarget?.reachable && previewTarget.url));
  const failedTargets = $derived.by(() => {
    const list = targets ? Object.entries(targets) : [];
    return list.filter(([, target]) => !target.reachable);
  });
  const primaryError = $derived(failedTargets[0]?.[1]?.error || 'Target preview belum bisa dijangkau.');

  function labelForTarget(key: string) {
    if (key === 'webrtcapi') return 'Preview WebRTC';
    if (key === 'dashboard_vendor') return 'Dashboard vendor';
    if (key === 'rtcpushapi') return 'RTC push';
    return key;
  }
</script>

<section class="panel" data-testid="performer-preview-panel">
  <div class="panel-head">
    <div>
      <h2>Preview</h2>
      <p>Tab ini mengecek reachability target vendor sebelum membuka preview avatar.</p>
    </div>
    <button class="btn btn-secondary" type="button" onclick={onRefresh} disabled={loading}>
      Cek Lagi
    </button>
  </div>

  {#if loading}
    <div class="card">
      <p class="muted">Sedang memeriksa target preview...</p>
    </div>
  {:else if previewReady && previewTarget}
    <div class="embed-shell">
      <iframe title="Preview avatar" src={previewTarget.url}></iframe>
    </div>
    <div class="actions">
      <a class="btn btn-secondary" href={previewTarget.url} target="_blank" rel="noopener">Buka Paksa di Tab Baru</a>
      {#if checkedAt}
        <span class="muted">Dicek {new Date(checkedAt).toLocaleTimeString()}</span>
      {/if}
    </div>
  {:else}
    <div class="fallback-card">
      <h3>Preview belum bisa dibuka</h3>
      <p>Dashboard menahan embed karena target vendor belum merespons normal.</p>
      <p class="primary-error">{primaryError}</p>
      {#if checkedAt}
        <p class="muted">Pengecekan terakhir {new Date(checkedAt).toLocaleTimeString()}</p>
      {/if}

      <div class="target-list">
        {#each failedTargets as [key, target]}
          <div class="target-row">
            <div>
              <strong>{labelForTarget(key)}</strong>
              <p>{target.http_status ? `HTTP ${target.http_status}` : 'Tidak terjangkau'}</p>
            </div>
            <a class="btn btn-secondary" href={target.url} target="_blank" rel="noopener">Buka Paksa di Tab Baru</a>
          </div>
        {/each}
      </div>

      <p class="next-step">
        Tindakan berikutnya: pastikan proses vendor pada port preview aktif, lalu jalankan pemeriksaan ulang.
      </p>
    </div>
  {/if}
</section>

<style>
  .panel,
  .fallback-card,
  .card {
    display: grid;
    gap: 16px;
  }

  .panel-head {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
  }

  .panel-head h2,
  .fallback-card h3 {
    margin: 0 0 6px;
    color: var(--text);
  }

  .panel-head p,
  .fallback-card p,
  .muted {
    margin: 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .card,
  .fallback-card {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    padding: 18px;
  }

  .fallback-card {
    border-color: rgba(245, 158, 11, 0.4);
    background: linear-gradient(180deg, rgba(245, 158, 11, 0.12), rgba(15, 23, 42, 0.82));
  }

  .primary-error {
    color: var(--text);
    font-weight: 700;
  }

  .embed-shell {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    overflow: hidden;
    background: #0f172a;
    min-height: 520px;
  }

  iframe {
    width: 100%;
    min-height: 520px;
    border: 0;
    background: #020617;
  }

  .target-list {
    display: grid;
    gap: 12px;
  }

  .target-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    padding: 14px;
    border-radius: 14px;
    background: rgba(0, 0, 0, 0.22);
  }

  .target-row strong {
    color: var(--text);
  }

  .actions {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
  }

  .next-step {
    color: var(--text);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    border: 1px solid var(--border);
    padding: 11px 14px;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
  }

  .btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text);
  }

  @media (max-width: 720px) {
    .panel-head,
    .target-row {
      flex-direction: column;
    }
  }
</style>
