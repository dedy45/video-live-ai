<script lang="ts">
  import type { EngineStatus, RuntimeTruth } from '../../lib/types';

  interface Props {
    truth: RuntimeTruth | null;
    engineStatus: EngineStatus | null;
    busyAction: string;
    onStart: () => void | Promise<void>;
    onStop: () => void | Promise<void>;
    onValidate: () => void | Promise<void>;
  }

  let { truth, engineStatus, busyAction, onStart, onStop, onValidate }: Props = $props();

  const face = $derived(truth?.face_engine);
  const faceState = $derived(face?.engine_state || engineStatus?.state || 'unknown');
  const faceRunning = $derived(faceState === 'running');
  const busy = $derived(busyAction !== '');

  function stateLabel(state: string) {
    if (state === 'running') return 'Berjalan';
    if (state === 'stopped') return 'Berhenti';
    if (state === 'starting' || state === 'warming') return 'Sedang memulai';
    return 'Belum diketahui';
  }
</script>

<section class="panel" data-testid="engine-panel">
  <div class="panel-head">
    <div>
      <h2>Avatar</h2>
      <p>Status avatar disinkronkan dari runtime truth dan status engine terbaru.</p>
    </div>
    <div class="status-pill">{stateLabel(faceState)}</div>
  </div>

  <div class="hero-grid">
    <article class="hero-card">
      <span class="eyebrow">Model aktif</span>
      <strong>{face?.resolved_model || engineStatus?.resolved_model || engineStatus?.model || 'Belum diketahui'}</strong>
      <p>Diminta {face?.requested_model || engineStatus?.requested_model || engineStatus?.model || 'unknown'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Avatar aktif</span>
      <strong>{face?.resolved_avatar_id || engineStatus?.resolved_avatar_id || engineStatus?.avatar_id || 'Belum diketahui'}</strong>
      <p>Diminta {face?.requested_avatar_id || engineStatus?.requested_avatar_id || engineStatus?.avatar_id || 'unknown'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Runtime</span>
      <strong>{truth?.face_runtime_mode || 'Belum diketahui'}</strong>
      <p>Transport {engineStatus?.transport || 'Belum diketahui'} · Port {engineStatus?.port ?? '—'}</p>
    </article>
  </div>

  <div class="grid">
    <article class="card">
      <h3>Kontrol Avatar</h3>
      <div class="button-stack">
        {#if faceRunning}
          <button class="btn btn-danger" type="button" onclick={onStop} disabled={busy}>
            Hentikan Avatar
          </button>
        {:else}
          <button class="btn btn-primary" type="button" onclick={onStart} disabled={busy}>
            Jalankan Avatar
          </button>
        {/if}
        <button class="btn btn-secondary" type="button" onclick={onValidate} disabled={busy}>
          Cek Engine Avatar
        </button>
      </div>
    </article>

    <article class="card">
      <h3>Path dan Runtime</h3>
      <div class="metric-list">
        <div><span>app.py</span><strong>{engineStatus?.app_py_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>Model</span><strong>{engineStatus?.model_path_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>Avatar</span><strong>{engineStatus?.avatar_path_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>Error terakhir</span><strong>{engineStatus?.last_error || 'Tidak ada'}</strong></div>
      </div>
    </article>
  </div>
</section>

<style>
  .panel {
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
  .card h3 {
    margin: 0 0 6px;
    color: var(--text);
  }

  .panel-head p {
    margin: 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .status-pill {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.05);
    font-weight: 700;
  }

  .hero-grid,
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
  }

  .hero-card,
  .card {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    padding: 18px;
  }

  .eyebrow {
    display: block;
    margin-bottom: 8px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
  }

  .hero-card strong {
    display: block;
    font-size: 24px;
    color: var(--text);
  }

  .hero-card p {
    margin: 6px 0 0;
    color: var(--muted);
  }

  .button-stack {
    display: grid;
    gap: 10px;
    margin-top: 12px;
  }

  .metric-list {
    display: grid;
    gap: 10px;
    margin-top: 12px;
  }

  .metric-list div {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .metric-list span {
    color: var(--muted);
  }

  .metric-list strong {
    color: var(--text);
    text-align: right;
  }

  .btn {
    border-radius: 12px;
    border: 1px solid var(--border);
    padding: 11px 14px;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }

  .btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .btn-primary {
    background: var(--accent);
    color: #000;
  }

  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text);
  }

  .btn-danger {
    background: #f59e0b;
    color: #111827;
  }
</style>
