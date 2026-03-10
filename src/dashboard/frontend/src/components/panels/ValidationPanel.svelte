<script lang="ts">
  import { onMount } from 'svelte';
  import {
    validateMockStack,
    validateLiveTalkingEngine,
    validateRtmpTarget,
    validateRuntimeTruth,
    validateRealModeReadiness,
    validateVoiceLocalClone,
    validateAudioChunkingSmoke,
    validateStreamDryRun,
    validateResourceBudget,
    validateSoakSanity,
    getValidationHistory,
  } from '../../lib/api';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';

  let history = $state<any[]>([]);
  let loading = $state(false);
  let receipt = $state<ReceiptType | null>(null);
  let activeResult = $state<Record<string, any> | null>(null);
  let loadedAt = $state<string | null>(null);

  async function loadHistory() {
    try {
      const data = await getValidationHistory();
      history = data.slice(0, 20);
      loadedAt = new Date().toISOString();
    } catch {
      // history load failure is non-critical
    }
  }

  async function runCheck(name: string, checkFn: () => Promise<any>, actionKey: string) {
    receipt = null;
    loading = true;
    try {
      const result = await checkFn();
      activeResult = { ...result, name };
      receipt = {
        action: `validate.${actionKey}`,
        status: result.status === 'error' ? 'error' : 'success',
        message: `${name}: ${result.status.toUpperCase()}`,
        timestamp: Date.now(),
      };
      await loadHistory();
    } catch (e: any) {
      receipt = {
        action: `validate.${actionKey}`,
        status: 'error',
        message: e.message,
        timestamp: Date.now(),
      };
    } finally {
      loading = false;
    }
  }

  onMount(loadHistory);
</script>

<div class="panel" data-testid="validation-panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Validation Gate Center</h2>
      <p class="panel-subtitle">Run the local-to-live gate checks before promotion, dry-run, and recovery work.</p>
    </div>
    <div class="panel-meta">
      <FreshnessBadge timestamp={loadedAt} />
    </div>
  </div>

  <ActionReceipt {receipt} />

  <div class="section-stack">
    <section class="gate-group">
      <div class="group-title">Core truth and readiness</div>
      <div class="grid">
        <div class="card"><div class="card-title">Runtime Truth</div><p class="desc">Check env consistency</p><button class="btn btn-ghost" data-testid="run-runtime-truth" onclick={() => runCheck('Runtime Truth', validateRuntimeTruth, 'runtime-truth')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Real-Mode Readiness</div><p class="desc">Final go/no-go checks</p><button class="btn btn-ghost" data-testid="run-real-mode" onclick={() => runCheck('Real-Mode Readiness', validateRealModeReadiness, 'real-mode')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Mock Stack</div><p class="desc">Check local mock services</p><button class="btn btn-ghost" data-testid="run-mock-stack" onclick={() => runCheck('Mock Stack', validateMockStack, 'mock-stack')} disabled={loading}>Run Check</button></div>
      </div>
    </section>

    <section class="gate-group">
      <div class="group-title">Voice and media checks</div>
      <div class="grid">
        <div class="card"><div class="card-title">Voice Local Clone</div><p class="desc">Verify local voice reference path</p><button class="btn btn-ghost" onclick={() => runCheck('Voice Local Clone', validateVoiceLocalClone, 'voice-local-clone')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Audio Chunking Smoke</div><p class="desc">Check chunk sizing for local synthesis</p><button class="btn btn-ghost" onclick={() => runCheck('Audio Chunking Smoke', validateAudioChunkingSmoke, 'audio-chunking-smoke')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">LiveTalking Engine</div><p class="desc">Test local engine readiness</p><button class="btn btn-ghost" data-testid="run-live-talking" onclick={() => runCheck('LiveTalking Engine', validateLiveTalkingEngine, 'livetalking')} disabled={loading}>Run Check</button></div>
      </div>
    </section>

    <section class="gate-group">
      <div class="group-title">Stream and long-run checks</div>
      <div class="grid">
        <div class="card"><div class="card-title">RTMP Target</div><p class="desc">Verify stream destination</p><button class="btn btn-ghost" data-testid="run-rtmp-target" onclick={() => runCheck('RTMP Target', validateRtmpTarget, 'rtmp')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Stream Dry Run</div><p class="desc">Exercise stream path without going live</p><button class="btn btn-ghost" onclick={() => runCheck('Stream Dry Run', validateStreamDryRun, 'stream-dry-run')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Resource Budget</div><p class="desc">Validate CPU, RAM, disk, and VRAM signals</p><button class="btn btn-ghost" onclick={() => runCheck('Resource Budget', validateResourceBudget, 'resource-budget')} disabled={loading}>Run Check</button></div>
        <div class="card"><div class="card-title">Soak Sanity</div><p class="desc">Check incident and recovery summary before long runs</p><button class="btn btn-ghost" onclick={() => runCheck('Soak Sanity', validateSoakSanity, 'soak-sanity')} disabled={loading}>Run Check</button></div>
      </div>
    </section>
  </div>

  {#if activeResult}
    <div class="detail-card card" data-testid="validation-detail">
      <div class="detail-header">
        <div class="card-title">{activeResult.name} Result</div>
        <span class="status-badge" class:status-pass={activeResult.status === 'pass'} class:status-fail={activeResult.status === 'fail' || activeResult.status === 'error'} class:status-blocked={activeResult.status === 'blocked'}>{activeResult.status}</span>
      </div>
      {#if activeResult.evidence_id}<p class="evidence">Evidence ID: <code>{activeResult.evidence_id}</code></p>{/if}
      <div class="checks-list">
        {#each activeResult.checks || [] as check}
          <div class="check-item">
            <span class="indicator" class:passed={check.passed}>{check.passed ? '●' : '○'}</span>
            <span class="check-name">{check.check}</span>
            <span class="check-msg">{check.message}</span>
          </div>
        {/each}
      </div>
      {#if activeResult.blockers && activeResult.blockers.length > 0}
        <div class="blockers"><div class="blockers-title">Blockers</div><ul>{#each activeResult.blockers as blocker}<li>{blocker}</li>{/each}</ul></div>
      {/if}
    </div>
  {/if}

  <section class="history-section" data-testid="validation-history">
    <div class="section-title">Recent validation history</div>
    <div class="history-list">
      {#each history as entry}
        <div class="history-row">
          <span class="hist-name">{entry.check_name}</span>
          <span class="hist-status" class:status-pass={entry.status === 'pass'} class:status-fail={entry.status === 'fail' || entry.status === 'error'} class:status-blocked={entry.status === 'blocked'}>{entry.status}</span>
          <ProvenanceBadge provenance={entry.provenance} />
          <span class="hist-time">{new Date(entry.timestamp).toLocaleTimeString()}</span>
        </div>
      {:else}
        <p class="muted">No validation history found.</p>
      {/each}
    </div>
  </section>
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; }
  .panel-meta { display: flex; align-items: center; gap: 8px; }
  .section-stack { display: flex; flex-direction: column; gap: 18px; margin-bottom: 18px; }
  .group-title, .section-title, .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 10px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 16px; border: 1px solid var(--border); }
  .desc { font-size: 12px; color: var(--muted); margin: 8px 0 12px; }
  .btn { padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--rsm); cursor: pointer; font-weight: 700; font-family: inherit; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn-ghost { width: 100%; background: rgba(255,255,255,.05); color: var(--text); }
  .detail-card { margin-bottom: 20px; }
  .detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .status-badge { text-transform: uppercase; font-size: 10px; font-weight: 800; padding: 3px 8px; border-radius: 4px; }
  .status-pass { background: rgba(0,230,118,.15); color: var(--green); }
  .status-fail { background: rgba(233,69,96,.15); color: var(--accent); }
  .status-blocked { background: rgba(255,214,0,.15); color: var(--yellow); }
  .evidence { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  .checks-list { display: flex; flex-direction: column; gap: 6px; }
  .check-item { display: flex; align-items: center; gap: 10px; font-size: 12px; }
  .indicator { color: var(--accent); font-weight: 800; }
  .indicator.passed { color: var(--green); }
  .check-name { min-width: 140px; font-weight: 700; }
  .check-msg { color: var(--muted); }
  .blockers { margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border); }
  .blockers-title { font-size: 12px; color: var(--accent); font-weight: 700; margin-bottom: 6px; }
  .blockers ul { margin: 0; padding-left: 18px; color: var(--accent); }
  .history-list { display: flex; flex-direction: column; gap: 6px; }
  .history-row { display: flex; align-items: center; gap: 14px; padding: 10px 14px; background: var(--card); border-radius: var(--rsm); border: 1px solid var(--border); font-size: 12px; }
  .hist-name { font-weight: 700; flex: 1; }
  .hist-status { width: 60px; font-weight: 700; text-transform: uppercase; font-size: 10px; }
  .hist-time { font-family: monospace; color: var(--muted); font-size: 10px; }
  .muted { color: var(--muted); }
</style>
