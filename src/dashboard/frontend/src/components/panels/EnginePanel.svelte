<script lang="ts">
  import { onMount } from 'svelte';
  import { getLiveTalkingStatus, getLiveTalkingConfig, getLiveTalkingLogs, startLiveTalking, stopLiveTalking, validateLiveTalkingEngine, getRuntimeTruth } from '../../lib/api';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let status = $state<Record<string, any>>({});
  let config = $state<Record<string, any>>({});
  let truth = $state<Record<string, any> | null>(null);
  let logs = $state<string[]>([]);
  let loading = $state(true);
  let actionLoading = $state(false);
  let error = $state('');
  let validationResult = $state<Record<string, any> | null>(null);
  let loadedAt = $state<string | null>(null);
  let receipt = $state<ReceiptType | null>(null);

  async function refresh() {
    loading = true;
    error = '';
    try {
      const [s, c, l, t] = await Promise.all([getLiveTalkingStatus(), getLiveTalkingConfig(), getLiveTalkingLogs(), getRuntimeTruth()]);
      status = s;
      config = c;
      logs = l.lines || [];
      truth = t;
      loadedAt = new Date().toISOString();
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function handleStart() {
    actionLoading = true;
    receipt = null;
    try {
      status = await startLiveTalking();
      receipt = { action: 'engine.start', status: 'success', message: `Engine started (state: ${status.state})`, timestamp: Date.now() };
    } catch (e: any) {
      error = e.message;
      receipt = { action: 'engine.start', status: 'error', message: e.message, timestamp: Date.now() };
    } finally {
      actionLoading = false;
    }
  }

  async function handleStop() {
    actionLoading = true;
    receipt = null;
    try {
      status = await stopLiveTalking();
      receipt = { action: 'engine.stop', status: 'success', message: 'Engine stopped', timestamp: Date.now() };
    } catch (e: any) {
      error = e.message;
      receipt = { action: 'engine.stop', status: 'error', message: e.message, timestamp: Date.now() };
    } finally {
      actionLoading = false;
    }
  }

  async function handleValidate() {
    receipt = null;
    try {
      validationResult = await validateLiveTalkingEngine();
      receipt = { action: 'engine.validate', status: validationResult.status === 'pass' ? 'success' : 'error', message: `Validation: ${validationResult.status}`, timestamp: Date.now() };
    } catch (e: any) {
      error = e.message;
      receipt = { action: 'engine.validate', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  onMount(refresh);
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Face Engine Control Center</h2>
      <p class="panel-subtitle">Control and validate LiveTalking or MuseTalk face runtime, model/avatar selection, and diagnostics.</p>
    </div>
    <div class="panel-meta">
      <ProvenanceBadge provenance={truth?.provenance?.engine_status || 'unknown'} />
      <FreshnessBadge timestamp={loadedAt} />
      <div class="btn-row">
        <button class="btn btn-ghost btn-sm" onclick={refresh} disabled={loading}>Refresh</button>
        <button class="btn btn-ghost btn-sm" onclick={handleValidate}>Validate</button>
      </div>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading face engine control center...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="hero-grid">
      <section class="hero-card">
        <div class="eyebrow">Engine state</div>
        <div class="hero-value">{status.state?.toUpperCase() || 'UNKNOWN'}</div>
        <div class="hero-copy">Runtime {truth?.face_runtime_mode || 'unknown'} · PID {status.pid || '-'}</div>
      </section>
      <section class="hero-card">
        <div class="eyebrow">Face model</div>
        <div class="hero-value">{status.resolved_model || status.model || 'unknown'}</div>
        <div class="hero-copy">Avatar {status.resolved_avatar_id || status.avatar_id || 'unknown'}</div>
      </section>
    </div>

    <div class="section-grid">
      <section class="card">
        <div class="section-title">Controls</div>
        <div class="btn-row vertical">
          <button class="btn btn-start" onclick={handleStart} disabled={actionLoading || status.state === 'running'}>Start</button>
          <button class="btn btn-stop" onclick={handleStop} disabled={actionLoading || status.state !== 'running'}>Stop</button>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Transport / uptime</div>
        <div class="stack-list">
          <div class="stack-row"><span>Port</span><strong>{status.port}</strong></div>
          <div class="stack-row"><span>Transport</span><strong>{status.transport}</strong></div>
          <div class="stack-row"><span>Uptime</span><strong>{(status.uptime_sec || 0).toFixed(0)}s</strong></div>
        </div>
      </section>

      <section class="card span-2">
        <div class="section-title">Model / avatar resolution</div>
        <div class="stats-grid">
          <div class="stat"><span class="label">Requested Model</span><span class="value small">{status.requested_model || status.model}</span></div>
          <div class="stat"><span class="label">Resolved Model</span><span class="value small">{status.resolved_model || status.model}</span></div>
          <div class="stat"><span class="label">Requested Avatar</span><span class="value small">{status.requested_avatar_id || status.avatar_id}</span></div>
          <div class="stat"><span class="label">Resolved Avatar</span><span class="value small">{status.resolved_avatar_id || status.avatar_id}</span></div>
          {#if status.requested_model && status.resolved_model && status.requested_model !== status.resolved_model}
            <div class="stat"><span class="label">Fallback</span><span class="value small">{status.requested_model} → {status.resolved_model}</span></div>
          {/if}
          {#if status.requested_avatar_id && status.resolved_avatar_id && status.requested_avatar_id !== status.resolved_avatar_id}
            <div class="stat"><span class="label">Fallback</span><span class="value small">{status.requested_avatar_id} → {status.resolved_avatar_id}</span></div>
          {/if}
        </div>
      </section>

      <section class="card">
        <div class="section-title">Path readiness</div>
        <div class="stack-list">
          <div class="stack-row"><span>app.py</span><strong>{status.app_py_exists ? 'Found' : 'Missing'}</strong></div>
          <div class="stack-row"><span>Models</span><strong>{status.model_path_exists ? 'Found' : 'Missing'}</strong></div>
          <div class="stack-row"><span>Avatar</span><strong>{status.avatar_path_exists ? 'Found' : 'Missing'}</strong></div>
        </div>
      </section>

      <section class="card">
        <div class="section-title">Vendor debug links</div>
        <div class="btn-row vertical">
          <a href={config.debug_urls?.dashboard_vendor} target="_blank" rel="noopener" class="btn btn-ghost">Vendor Dashboard</a>
          <a href={config.debug_urls?.webrtcapi} target="_blank" rel="noopener" class="btn btn-ghost">WebRTC Preview</a>
          <a href={config.debug_urls?.rtcpushapi} target="_blank" rel="noopener" class="btn btn-ghost">RTC Push</a>
        </div>
      </section>
    </div>

    {#if status.last_error}
      <div class="error-box"><strong>Last Error:</strong> {status.last_error}</div>
    {/if}

    {#if validationResult}
      <div class="validation-result" class:pass={validationResult.status === 'pass'} class:fail={validationResult.status !== 'pass'}>
        <h3>Validation: {validationResult.status?.toUpperCase()}</h3>
        {#each validationResult.checks || [] as check}
          <div class="check-row" class:passed={check.passed} class:failed={!check.passed}>
            <span>{check.passed ? '●' : '○'}</span>
            <span>{check.check}</span>
            <span class="muted">{check.message}</span>
          </div>
        {/each}
      </div>
    {/if}

    {#if logs.length > 0}
      <div class="card logs-section">
        <div class="section-title">Engine logs</div>
        <div class="log-viewer">{#each logs as line}<div class="log-line">{line}</div>{/each}</div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; }
  .panel-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .hero-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .hero-card, .card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .eyebrow, .section-title, .label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 32px; font-weight: 900; margin: 8px 0; word-break: break-word; }
  .hero-copy { color: var(--muted); font-size: 13px; }
  .section-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
  .span-2 { grid-column: span 2; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 12px; }
  .stat { padding: 12px; border-radius: var(--rsm); background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.04); }
  .value { display: block; margin-top: 6px; font-size: 22px; font-weight: 800; color: var(--text); }
  .value.small { font-size: 14px; font-weight: 700; line-height: 1.5; }
  .stack-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
  .stack-row { display: flex; justify-content: space-between; gap: 12px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,.05); }
  .btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn-row.vertical { display: grid; }
  .btn { padding: 10px 14px; border-radius: var(--rsm); border: 1px solid var(--border); cursor: pointer; font-weight: 700; font-family: inherit; text-decoration: none; text-align: center; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn-ghost { background: rgba(255,255,255,.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-start { background: var(--green); color: #000; }
  .btn-stop { background: var(--yellow); color: #000; }
  .error-box { background: rgba(233,69,96,.1); border: 1px solid rgba(233,69,96,.3); border-radius: var(--rsm); padding: 12px; margin: 14px 0; color: var(--accent); }
  .validation-result { padding: 14px; border-radius: var(--rsm); margin-bottom: 14px; }
  .validation-result.pass { background: rgba(0,230,118,.05); border: 1px solid rgba(0,230,118,.2); }
  .validation-result.fail { background: rgba(233,69,96,.05); border: 1px solid rgba(233,69,96,.2); }
  .validation-result h3 { font-size: 14px; margin-bottom: 8px; }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding: 4px 0; }
  .check-row.passed { color: var(--green); }
  .check-row.failed { color: var(--accent); }
  .logs-section { margin-top: 14px; }
  .log-viewer { max-height: 250px; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; background: rgba(0,0,0,.3); border-radius: var(--rsm); padding: 10px; }
  .log-line { padding: 2px 0; color: var(--muted); white-space: pre-wrap; word-break: break-all; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
  @media (max-width: 1024px) { .section-grid { grid-template-columns: 1fr; } .span-2 { grid-column: span 1; } }
</style>
