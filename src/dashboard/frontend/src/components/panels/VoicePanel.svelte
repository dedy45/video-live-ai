<script lang="ts">
  import type { RuntimeTruth, VoiceTestSpeakResult } from '../../lib/types';

  interface Props {
    truth: RuntimeTruth | null;
    busyAction: string;
    voiceTestResult: VoiceTestSpeakResult | null;
    onWarmup: () => void | Promise<void>;
    onRestart: () => void | Promise<void>;
    onClearQueue: () => void | Promise<void>;
    onTestSpeak: (text: string) => void | Promise<void>;
  }

  let {
    truth,
    busyAction,
    voiceTestResult,
    onWarmup,
    onRestart,
    onClearQueue,
    onTestSpeak,
  }: Props = $props();

  let testText = $state('Halo operator');

  const voice = $derived(truth?.voice_engine);
  const busy = $derived(busyAction !== '');
  const voiceStatus = $derived.by(() => {
    if (!voice) return { label: 'Belum ada data', summary: 'Snapshot suara belum tersedia.' };
    if (voice.server_reachable && voice.reference_ready) {
      return { label: 'Siap', summary: 'Mesin suara terhubung dan referensi sudah siap.' };
    }
    if (!voice.server_reachable) {
      return { label: 'Tertahan', summary: 'Sidecar suara belum bisa dijangkau.' };
    }
    if (!voice.reference_ready) {
      return { label: 'Perlu referensi', summary: 'Referensi suara belum siap dipakai.' };
    }
    return { label: 'Belum aktif', summary: 'Mesin suara belum dipanaskan.' };
  });

  function submitVoiceTest() {
    onTestSpeak(testText.trim() || 'Halo operator');
  }
</script>

<section class="panel" data-testid="voice-panel">
  <div class="panel-head">
    <div>
      <h2>Suara</h2>
      <p>{voiceStatus.summary}</p>
    </div>
    <div class="status-pill">{voiceStatus.label}</div>
  </div>

  <div class="hero-grid">
    <article class="hero-card">
      <span class="eyebrow">Mesin</span>
      <strong>{voice?.resolved_engine || 'Belum diketahui'}</strong>
      <p>Diminta {voice?.requested_engine || 'unknown'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Referensi</span>
      <strong>{voice?.reference_ready ? 'Siap' : 'Belum siap'}</strong>
      <p>{voice?.server_reachable ? 'Server terjangkau' : 'Server belum terjangkau'}</p>
    </article>
    <article class="hero-card">
      <span class="eyebrow">Antrian</span>
      <strong>{voice?.queue_depth ?? 0}</strong>
      <p>Latency terakhir {voice?.last_latency_ms ? `${voice.last_latency_ms} ms` : 'belum ada data'}</p>
    </article>
  </div>

  <div class="grid">
    <article class="card">
      <h3>Kontrol Operator</h3>
      <div class="button-stack">
        <button class="btn btn-primary" type="button" onclick={onWarmup} disabled={busy}>
          Panaskan Mesin Suara
        </button>
        <button class="btn btn-secondary" type="button" onclick={onRestart} disabled={busy}>
          Mulai Ulang Mesin Suara
        </button>
        <button class="btn btn-secondary" type="button" onclick={onClearQueue} disabled={busy}>
          Kosongkan Antrian Suara
        </button>
      </div>
    </article>

    <article class="card">
      <h3>Telemetri</h3>
      <div class="metric-list">
        <div><span>Chunk audio</span><strong>{voice?.chunk_chars ?? '—'}</strong></div>
        <div><span>Latency p50 / p95</span><strong>{voice?.latency_p50_ms ?? '—'} / {voice?.latency_p95_ms ?? '—'} ms</strong></div>
        <div><span>Audio pertama</span><strong>{voice?.time_to_first_audio_ms ?? '—'} ms</strong></div>
        <div><span>Error terakhir</span><strong>{voice?.last_error || 'Tidak ada'}</strong></div>
      </div>
    </article>
  </div>

  <article class="card">
    <h3>Tes Suara</h3>
    <p class="card-copy">Masukkan kalimat singkat untuk memastikan sintesis suara merespons normal.</p>
    <div class="test-row">
      <input
        bind:value={testText}
        placeholder="Masukkan teks untuk disintesis"
        disabled={busy}
      />
      <button class="btn btn-primary" type="button" onclick={submitVoiceTest} disabled={busy}>
        Tes Suara
      </button>
    </div>

    {#if voiceTestResult}
      <div class="telemetry-strip">
        <span>Latency {voiceTestResult.latency_ms ?? '—'} ms</span>
        <span>Durasi {voiceTestResult.duration_ms ?? '—'} ms</span>
        <span>Ukuran audio {voiceTestResult.audio_length_bytes ?? '—'} bytes</span>
      </div>
    {/if}
  </article>
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
  .card-copy {
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

  .test-row {
    display: flex;
    gap: 12px;
    margin-top: 12px;
  }

  .test-row input {
    flex: 1;
    min-width: 0;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.03);
    color: var(--text);
    font: inherit;
  }

  .telemetry-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
    color: var(--muted);
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

  @media (max-width: 720px) {
    .test-row {
      flex-direction: column;
    }
  }
</style>
