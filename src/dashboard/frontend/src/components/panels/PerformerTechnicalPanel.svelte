<script lang="ts">
  import type { EngineConfig, EngineStatus, LiveTalkingDebugTargets, RuntimeTruth } from '../../lib/types';

  interface Props {
    truth: RuntimeTruth | null;
    config: EngineConfig | null;
    engineStatus: EngineStatus | null;
    engineLogs: string[];
    debugTargets: LiveTalkingDebugTargets | null;
    loading: boolean;
    error: string;
    onRefresh: () => void | Promise<void>;
  }

  let {
    truth,
    config,
    engineStatus,
    engineLogs,
    debugTargets,
    loading,
    error,
    onRefresh,
  }: Props = $props();
</script>

<section class="panel" data-testid="performer-technical-panel">
  <div class="panel-head">
    <div>
      <h2>Teknis</h2>
      <p>Log, path readiness, vendor URL, dan snapshot truth ringkas untuk troubleshooting operator lanjutan.</p>
    </div>
    <button class="btn" type="button" onclick={onRefresh} disabled={loading}>
      Muat Ulang Teknis
    </button>
  </div>

  {#if error}
    <div class="alert">{error}</div>
  {/if}

  <div class="grid">
    <article class="card">
      <h3>Status Engine</h3>
      <div class="metric-list">
        <div><span>State</span><strong>{engineStatus?.state || truth?.face_engine?.engine_state || 'Belum diketahui'}</strong></div>
        <div><span>PID</span><strong>{engineStatus?.pid ?? '—'}</strong></div>
        <div><span>Port</span><strong>{engineStatus?.port ?? config?.port ?? '—'}</strong></div>
        <div><span>Transport</span><strong>{engineStatus?.transport || config?.transport || '—'}</strong></div>
      </div>
    </article>

    <article class="card">
      <h3>Path Readiness</h3>
      <div class="metric-list">
        <div><span>app.py</span><strong>{engineStatus?.app_py_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>Folder model</span><strong>{engineStatus?.model_path_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>Folder avatar</span><strong>{engineStatus?.avatar_path_exists ? 'Siap' : 'Belum ada'}</strong></div>
        <div><span>LiveTalking dir</span><strong>{config?.livetalking_dir || 'Belum diketahui'}</strong></div>
      </div>
    </article>

    <article class="card span-2">
      <h3>Vendor URLs</h3>
      <div class="url-list">
        {#if debugTargets}
          {#each Object.entries(debugTargets.targets) as [key, target]}
            <div class="url-row">
              <div>
                <strong>{key}</strong>
                <p>{target.url}</p>
              </div>
              <span class:ok={target.reachable} class:fail={!target.reachable}>
                {target.reachable ? 'Reachable' : target.error || 'Tidak terjangkau'}
              </span>
            </div>
          {/each}
        {/if}
      </div>
    </article>

    <article class="card span-2">
      <h3>Runtime Truth Ringkas</h3>
      <pre>{JSON.stringify(truth, null, 2)}</pre>
    </article>

    <article class="card span-2">
      <h3>Log Engine</h3>
      <pre>{engineLogs.length > 0 ? engineLogs.join('\n') : 'Belum ada log engine.'}</pre>
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

  .panel-head p,
  .card p {
    margin: 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 14px;
  }

  .span-2 {
    grid-column: span 2;
  }

  .card {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    padding: 18px;
    display: grid;
    gap: 12px;
  }

  .metric-list,
  .url-list {
    display: grid;
    gap: 10px;
  }

  .metric-list div,
  .url-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .metric-list span,
  .url-row p {
    color: var(--muted);
  }

  .metric-list strong,
  .url-row strong {
    color: var(--text);
  }

  .ok {
    color: #6ee7b7;
  }

  .fail {
    color: #fca5a5;
  }

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-size: 12px;
    color: var(--muted);
    background: rgba(0, 0, 0, 0.22);
    padding: 12px;
    border-radius: 14px;
    overflow: auto;
    max-height: 280px;
  }

  .alert {
    border-radius: 14px;
    border: 1px solid rgba(239, 68, 68, 0.4);
    background: rgba(239, 68, 68, 0.12);
    color: #fca5a5;
    padding: 12px 14px;
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

  @media (max-width: 900px) {
    .span-2 {
      grid-column: span 1;
    }

    .panel-head,
    .url-row {
      flex-direction: column;
    }
  }
</style>
