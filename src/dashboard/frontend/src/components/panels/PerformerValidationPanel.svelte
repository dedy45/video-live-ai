<script lang="ts">
  import type { PerformerValidationCheckId, PerformerValidationEntry } from '../../lib/types';

  interface Props {
    runningCheck: string;
    results: Partial<Record<PerformerValidationCheckId, PerformerValidationEntry>>;
    onRunCheck: (checkId: PerformerValidationCheckId) => void | Promise<void>;
  }

  let { runningCheck, results, onRunCheck }: Props = $props();

  const checks: Array<{ id: PerformerValidationCheckId; label: string; summary: string }> = [
    { id: 'real_mode', label: 'Cek Kesiapan Runtime', summary: 'Memastikan prasyarat domain avatar dan suara siap dipakai.' },
    { id: 'engine', label: 'Cek Engine Avatar', summary: 'Memeriksa status runtime avatar, model, avatar, dan path penting.' },
    { id: 'voice_clone', label: 'Cek Clone Suara Lokal', summary: 'Memeriksa sidecar suara dan kesiapan referensi clone.' },
    { id: 'audio_chunking', label: 'Cek Chunking Audio', summary: 'Memastikan chunking audio masih sehat untuk pipeline suara.' },
    { id: 'runtime_truth', label: 'Cek Runtime Truth', summary: 'Memastikan dashboard membaca source of truth yang konsisten.' },
    { id: 'preview_targets', label: 'Cek Target Preview', summary: 'Memeriksa apakah preview vendor benar-benar bisa dijangkau.' },
  ];

  function statusLabel(status: PerformerValidationEntry['status']) {
    if (status === 'pass') return 'Lulus';
    if (status === 'blocked') return 'Tertahan';
    if (status === 'pending') return 'Berjalan';
    if (status === 'error') return 'Error';
    return 'Gagal';
  }
</script>

<section class="panel" data-testid="performer-validation-panel">
  <div class="panel-head">
    <div>
      <h2>Validasi</h2>
      <p>Gunakan tab ini untuk pemeriksaan cepat domain avatar dan suara tanpa pindah ke menu lain.</p>
    </div>
    <a class="shortcut-link" href="#/setup">Buka Setup & Validasi</a>
  </div>

  <div class="grid">
    {#each checks as check}
      <article class="card">
        <div class="card-head">
          <div>
            <h3>{check.label}</h3>
            <p>{check.summary}</p>
          </div>
          {#if results[check.id]}
            <span class="status-pill status-{results[check.id]?.status}">
              {statusLabel(results[check.id]!.status)}
            </span>
          {/if}
        </div>

        <button
          class="btn"
          type="button"
          onclick={() => onRunCheck(check.id)}
          disabled={runningCheck === check.id}
        >
          {check.label}
        </button>

        {#if results[check.id]}
          <div class="result-box">
            <p>{results[check.id]?.summary}</p>
            <span class="muted">Terakhir dicek {new Date(results[check.id]!.timestamp).toLocaleTimeString()}</span>
          </div>
        {/if}
      </article>
    {/each}
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

  .panel-head p,
  .card p,
  .muted {
    margin: 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .shortcut-link {
    color: var(--text);
    text-decoration: none;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.04);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
  }

  .card {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    padding: 18px;
    display: grid;
    gap: 14px;
  }

  .card-head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
  }

  .status-pill {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid transparent;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
  }

  .status-pass {
    border-color: rgba(16, 185, 129, 0.35);
    color: #6ee7b7;
  }

  .status-fail,
  .status-error {
    border-color: rgba(239, 68, 68, 0.35);
    color: #fca5a5;
  }

  .status-blocked {
    border-color: rgba(245, 158, 11, 0.35);
    color: #fcd34d;
  }

  .status-pending {
    border-color: rgba(59, 130, 246, 0.35);
    color: #93c5fd;
  }

  .btn {
    border-radius: 12px;
    border: 1px solid var(--border);
    padding: 11px 14px;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
    background: rgba(255, 255, 255, 0.05);
    color: var(--text);
  }

  .btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .result-box {
    border-radius: 14px;
    padding: 12px;
    background: rgba(255, 255, 255, 0.04);
    display: grid;
    gap: 6px;
  }

  @media (max-width: 720px) {
    .panel-head,
    .card-head {
      flex-direction: column;
    }
  }
</style>
