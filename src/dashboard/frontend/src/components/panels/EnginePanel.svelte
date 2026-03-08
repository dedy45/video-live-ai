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
      const [s, c, l, t] = await Promise.all([
        getLiveTalkingStatus(),
        getLiveTalkingConfig(),
        getLiveTalkingLogs(),
        getRuntimeTruth(),
      ]);
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
      receipt = { action: 'engine.stop', status: 'success', message: `Engine stopped`, timestamp: Date.now() };
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
    <h2 class="panel-title">LiveTalking Engine</h2>
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
    <p class="muted">Loading engine status...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <div class="card">
        <div class="card-title">State</div>
        <div class="engine-state" class:running={status.state === 'running'}
             class:stopped={status.state === 'stopped'}
             class:engine-error={status.state === 'error'}>
          {status.state?.toUpperCase() || 'UNKNOWN'}
        </div>
        <div class="btn-row">
          <button class="btn btn-start btn-sm" onclick={handleStart}
            disabled={actionLoading || status.state === 'running'}>Start</button>
          <button class="btn btn-stop btn-sm" onclick={handleStop}
            disabled={actionLoading || status.state !== 'running'}>Stop</button>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Engine Info</div>
        <div class="info-grid">
          <div class="info-row"><span class="info-label">Port</span><span>{status.port}</span></div>
          <div class="info-row"><span class="info-label">Transport</span><span>{status.transport}</span></div>
          <div class="info-row"><span class="info-label">Uptime</span><span>{(status.uptime_sec || 0).toFixed(0)}s</span></div>
          <div class="info-row"><span class="info-label">PID</span><span>{status.pid || '-'}</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Model / Avatar</div>
        <div class="info-grid">
          <div class="info-row"><span class="info-label">Requested Model</span><span>{status.requested_model || status.model}</span></div>
          <div class="info-row"><span class="info-label">Resolved Model</span><span>{status.resolved_model || status.model}</span></div>
          {#if status.requested_model && status.resolved_model && status.requested_model !== status.resolved_model}
            <div class="info-row fallback-warning"><span class="info-label">Fallback</span><span class="yellow">{status.requested_model} → {status.resolved_model}</span></div>
          {/if}
          <div class="info-row"><span class="info-label">Requested Avatar</span><span>{status.requested_avatar_id || status.avatar_id}</span></div>
          <div class="info-row"><span class="info-label">Resolved Avatar</span><span>{status.resolved_avatar_id || status.avatar_id}</span></div>
          {#if status.requested_avatar_id && status.resolved_avatar_id && status.requested_avatar_id !== status.resolved_avatar_id}
            <div class="info-row fallback-warning"><span class="info-label">Fallback</span><span class="yellow">{status.requested_avatar_id} → {status.resolved_avatar_id}</span></div>
          {/if}
        </div>
      </div>

      <div class="card">
        <div class="card-title">Path Readiness</div>
        <div class="info-grid">
          <div class="info-row">
            <span class="info-label">app.py</span>
            <span class:green={status.app_py_exists} class:red={!status.app_py_exists}>
              {status.app_py_exists ? 'Found' : 'Missing'}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">Models</span>
            <span class:green={status.model_path_exists} class:red={!status.model_path_exists}>
              {status.model_path_exists ? 'Found' : 'Missing'}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">Avatar</span>
            <span class:green={status.avatar_path_exists} class:red={!status.avatar_path_exists}>
              {status.avatar_path_exists ? 'Found' : 'Missing'}
            </span>
          </div>
        </div>
      </div>
    </div>

    {#if status.last_error}
      <div class="error-box">
        <strong>Last Error:</strong> {status.last_error}
      </div>
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

    {#if config.debug_urls}
      <div class="card vendor-links">
        <div class="card-title">Vendor Debug Links</div>
        <div class="btn-row">
          <a href={config.debug_urls.dashboard_vendor} target="_blank" rel="noopener" class="btn btn-ghost btn-sm">Vendor Dashboard</a>
          <a href={config.debug_urls.webrtcapi} target="_blank" rel="noopener" class="btn btn-ghost btn-sm">WebRTC Preview</a>
          <a href={config.debug_urls.rtcpushapi} target="_blank" rel="noopener" class="btn btn-ghost btn-sm">RTC Push</a>
        </div>
      </div>
    {/if}

    {#if logs.length > 0}
      <div class="card logs-section">
        <div class="card-title">Engine Logs (last {logs.length})</div>
        <div class="log-viewer">
          {#each logs as line}
            <div class="log-line">{line}</div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .card:hover { background: var(--card-hover); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px; }
  .engine-state { font-size: 22px; font-weight: 800; margin-bottom: 10px; }
  .engine-state.running { color: var(--green); }
  .engine-state.stopped { color: var(--muted); }
  .engine-state.engine-error { color: var(--accent); }
  .info-grid { display: flex; flex-direction: column; gap: 6px; }
  .info-row { display: flex; justify-content: space-between; font-size: 13px; }
  .info-label { color: var(--muted); }
  .error-box { background: rgba(233,69,96,.1); border: 1px solid rgba(233,69,96,.3); border-radius: var(--rsm); padding: 12px; margin-bottom: 14px; font-size: 13px; color: var(--accent); }
  .vendor-links { margin-bottom: 14px; }
  .vendor-links a { text-decoration: none; }
  .logs-section { margin-top: 14px; }
  .log-viewer { max-height: 250px; overflow-y: auto; font-family: 'Consolas', 'Monaco', monospace; font-size: 11px; background: rgba(0,0,0,.3); border-radius: var(--rsm); padding: 10px; }
  .log-line { padding: 2px 0; color: var(--muted); white-space: pre-wrap; word-break: break-all; }
  .validation-result { padding: 14px; border-radius: var(--rsm); margin-bottom: 14px; }
  .validation-result.pass { background: rgba(0,230,118,.05); border: 1px solid rgba(0,230,118,.2); }
  .validation-result.fail { background: rgba(233,69,96,.05); border: 1px solid rgba(233,69,96,.2); }
  .validation-result h3 { font-size: 14px; margin-bottom: 8px; }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding: 4px 0; }
  .check-row.passed { color: var(--green); }
  .check-row.failed { color: var(--accent); }
  .btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; display: inline-flex; align-items: center; gap: 5px; }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-ghost:hover { background: rgba(255,255,255,.1); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
  .btn-start { background: var(--green); color: #000; }
  .btn-stop { background: var(--yellow); color: #000; }
  .green { color: var(--green); }
  .red { color: var(--accent); }
  .yellow { color: var(--yellow); }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
  .fallback-warning { background: rgba(255,214,10,.06); border-radius: 4px; padding: 2px 4px; }
</style>
