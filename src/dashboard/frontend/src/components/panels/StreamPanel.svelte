<script lang="ts">
  import { onMount } from 'svelte';
  import {
    activateStreamTarget,
    createStreamTarget,
    emergencyReset,
    emergencyStop,
    getLiveSession,
    getPipelineState,
    getRuntimeTruth,
    getStatus,
    getStreamTargets,
    pauseLiveSession,
    pipelineTransition,
    resumeLiveSession,
    startLiveSession,
    stopLiveSession,
    updateStreamTarget,
    validateRtmpTarget,
    validateStreamDryRun,
    validateStreamTarget,
  } from '../../lib/api';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import FreshnessBadge from '../common/FreshnessBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import type { LiveSessionSummary, StreamTarget } from '../../lib/types';

  let status = $state<Record<string, any>>({});
  let truth = $state<Record<string, any> | null>(null);
  let pipeline = $state<Record<string, any> | null>(null);
  let liveSession = $state<LiveSessionSummary | null>(null);
  let streamTargets = $state<StreamTarget[]>([]);
  let validationResult = $state<Record<string, any> | null>(null);
  let loading = $state(true);
  let loadedAt = $state<string | null>(null);
  let receipt = $state<ReceiptType | null>(null);

  let editingTargetId = $state<number | null>(null);
  let selectedPlatform = $state('tiktok');
  let targetLabel = $state('');
  let rtmpUrl = $state('');
  let streamKey = $state('');

  const pipelineFallbacks: Record<string, string[]> = {
    IDLE: ['SELLING', 'PAUSED'],
    SELLING: ['REACTING', 'ENGAGING', 'PAUSED', 'IDLE'],
    REACTING: ['SELLING', 'ENGAGING', 'PAUSED'],
    ENGAGING: ['SELLING', 'REACTING', 'PAUSED'],
    PAUSED: ['IDLE', 'SELLING'],
    STOPPED: ['IDLE'],
  };

  function pipelineStateLabel() {
    return String(pipeline?.current_state || pipeline?.state || 'unknown').toUpperCase();
  }

  function pipelineTargets() {
    const current = pipelineStateLabel();
    const runtimeTransitions = Array.isArray(pipeline?.valid_transitions)
      ? pipeline.valid_transitions.map((target) => String(target).toUpperCase())
      : [];
    const nextTargets = runtimeTransitions.length > 0
      ? runtimeTransitions
      : (pipelineFallbacks[current] || []);
    return [...new Set([current, ...nextTargets].filter((target) => target && target !== 'UNKNOWN'))];
  }

  function activeTarget() {
    return streamTargets.find((target) => target.is_active) || null;
  }

  function syncFormFromTarget(target: StreamTarget) {
    editingTargetId = target.id;
    selectedPlatform = target.platform || 'tiktok';
    targetLabel = target.label || '';
    rtmpUrl = target.rtmp_url || '';
    streamKey = '';
  }

  function resetTargetForm() {
    editingTargetId = null;
    selectedPlatform = 'tiktok';
    targetLabel = '';
    rtmpUrl = '';
    streamKey = '';
  }

  async function refresh() {
    loading = true;
    try {
      const [nextStatus, nextTruth, nextPipeline, nextTargets, nextSession] = await Promise.all([
        getStatus(),
        getRuntimeTruth(),
        getPipelineState(),
        getStreamTargets(),
        getLiveSession(),
      ]);
      status = nextStatus;
      truth = nextTruth;
      pipeline = nextPipeline;
      streamTargets = nextTargets;
      liveSession = nextSession;
      loadedAt = new Date().toISOString();
    } catch (nextError: any) {
      receipt = { action: 'stream.refresh', status: 'error', message: nextError.message, timestamp: Date.now() };
    } finally {
      loading = false;
    }
  }

  async function handleAction(action: string, work: () => Promise<any>, successMessage: string) {
    receipt = null;
    try {
      const result = await work();
      const message = result?.message || successMessage;
      receipt = { action, status: 'success', message, timestamp: Date.now() };
      await refresh();
    } catch (nextError: any) {
      receipt = { action, status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleSaveTarget(event?: SubmitEvent) {
    event?.preventDefault();
    receipt = null;
    const payload = {
      platform: selectedPlatform,
      label: targetLabel.trim() || `${selectedPlatform.toUpperCase()} target`,
      rtmp_url: rtmpUrl.trim(),
      stream_key: streamKey.trim(),
    };

    try {
      if (editingTargetId !== null) {
        await updateStreamTarget(editingTargetId, payload);
        receipt = { action: 'stream_target.update', status: 'success', message: `Target ${payload.label} diperbarui.`, timestamp: Date.now() };
      } else {
        await createStreamTarget(payload);
        receipt = { action: 'stream_target.create', status: 'success', message: `Target ${payload.label} tersimpan.`, timestamp: Date.now() };
      }
      resetTargetForm();
      await refresh();
    } catch (nextError: any) {
      receipt = { action: 'stream_target.save', status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleValidateTarget(targetId?: number) {
    receipt = null;
    try {
      if (targetId) {
        validationResult = await validateStreamTarget(targetId);
      } else {
        validationResult = await validateRtmpTarget();
      }
      receipt = {
        action: 'stream_target.validate',
        status: validationResult.status === 'pass' ? 'success' : 'error',
        message: `RTMP validation: ${validationResult.status}`,
        timestamp: Date.now(),
      };
      await refresh();
    } catch (nextError: any) {
      receipt = { action: 'stream_target.validate', status: 'error', message: nextError.message, timestamp: Date.now() };
    }
  }

  async function handleStartSession() {
    await handleAction(
      'live_session.start',
      () => startLiveSession({ platform: selectedPlatform }),
      'Sesi live dimulai.',
    );
  }

  async function handlePauseSession() {
    await handleAction(
      'live_session.pause',
      () => pauseLiveSession({ reason: 'viewer_question', question: 'Pause rotasi untuk tanya jawab.' }),
      'Rotasi produk dipause untuk Q&A.',
    );
  }

  onMount(() => {
    void refresh();
  });
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Stream Control Center</h2>
      <p class="panel-subtitle">Kelola target RTMP yang tersimpan, validasi TikTok-first, dan operasi streaming dari dashboard yang menjadi source of truth.</p>
    </div>
    <div class="panel-meta">
      <ProvenanceBadge provenance={truth?.provenance?.stream_status || 'unknown'} />
      <FreshnessBadge timestamp={loadedAt} />
      <button class="btn btn-ghost btn-sm" onclick={refresh}>Refresh</button>
    </div>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading stream control center...</p>
  {:else}
    <div class="hero-grid">
      <section class="hero-card">
        <div class="eyebrow">Stream posture</div>
        <div class="hero-value">{status.stream_status || 'idle'}</div>
        <div class="hero-copy">Runtime {truth?.stream_runtime_mode || 'unknown'} · Pipeline {pipelineStateLabel()}</div>
      </section>
      <section class="hero-card" class:alert={status.emergency_stopped}>
        <div class="eyebrow">Sesi aktif</div>
        <div class="hero-value">{liveSession?.session ? 'LIVE' : 'IDLE'}</div>
        <div class="hero-copy">
          Mode {liveSession?.state?.current_mode || 'belum ada sesi'} · Target {liveSession?.stream_target?.label || activeTarget()?.label || 'belum aktif'}
        </div>
      </section>
    </div>

    <section class="card">
      <div class="section-title">RTMP Configuration</div>
      <form aria-label="RTMP Target" onsubmit={handleSaveTarget}>
        <div class="form-grid">
          <div class="form-group">
            <label for="platform-target">Platform</label>
            <select id="platform-target" class="form-input" bind:value={selectedPlatform}>
              <option value="tiktok">TikTok</option>
              <option value="shopee">Shopee</option>
            </select>
          </div>
          <div class="form-group">
            <label for="target-label">Label Target</label>
            <input id="target-label" class="form-input" bind:value={targetLabel} placeholder="Primary TikTok" autocomplete="off" />
          </div>
          <div class="form-group">
            <label for="rtmp-url">RTMP URL</label>
            <input id="rtmp-url" class="form-input" bind:value={rtmpUrl} placeholder="rtmp://push.tiktokcdn.com/live/" autocomplete="url" />
          </div>
          <div class="form-group">
            <label for="stream-key">Stream Key</label>
            <input id="stream-key" type="password" class="form-input" bind:value={streamKey} placeholder="Paste stream key dari platform" autocomplete="current-password" />
          </div>
        </div>
        <div class="rtmp-actions">
          <button type="submit" class="btn btn-switch">Simpan Target</button>
          <button type="button" class="btn btn-ghost" onclick={() => handleValidateTarget(activeTarget()?.id)}>Validate RTMP Target</button>
          <button type="button" class="btn btn-ghost" onclick={() => handleAction('stream.dry_run', validateStreamDryRun, 'Dry run selesai')}>Dry Run</button>
          {#if editingTargetId !== null}
            <button type="button" class="btn btn-ghost" onclick={resetTargetForm}>Batal Edit</button>
          {/if}
        </div>
      </form>
      {#if validationResult}
        <div class="result-box" class:pass={validationResult.status === 'pass'} class:fail={validationResult.status !== 'pass'}>
          <strong>{validationResult.status?.toUpperCase()}</strong>
          {#each validationResult.checks || [] as check}
            <div class="check-row">
              <span>{check.passed ? '●' : '○'}</span>
              <span>{check.check}</span>
              <span class="muted">{check.message}</span>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    <div class="section-grid">
      <section class="card">
        <div class="section-title">Target RTMP Tersimpan</div>
        <div class="target-list">
          {#each streamTargets as target}
            <div class="target-item">
              <div class="target-copy">
                <div class="target-title">{target.label}</div>
                <div class="target-meta">{target.platform} · {target.stream_key_masked} · {target.validation_status}</div>
              </div>
              <div class="target-actions">
                <button class="btn btn-ghost btn-sm" onclick={() => syncFormFromTarget(target)}>Edit</button>
                <button class="btn btn-ghost btn-sm" onclick={() => handleValidateTarget(target.id)}>Validate</button>
                <button class="btn btn-ghost btn-sm" onclick={() => handleAction('stream_target.activate', () => activateStreamTarget(target.id), `Target ${target.label} aktif.`)}>Aktifkan</button>
              </div>
            </div>
          {:else}
            <p class="muted">Belum ada target RTMP tersimpan.</p>
          {/each}
        </div>
      </section>

      <section class="card">
        <div class="section-title">Kontrol Sesi Live</div>
        <div class="summary-list">
          <div class="summary-row"><span>Status</span><strong>{liveSession?.session?.status || 'idle'}</strong></div>
          <div class="summary-row"><span>Mode</span><strong>{liveSession?.state?.current_mode || 'unknown'}</strong></div>
          <div class="summary-row"><span>Pause</span><strong>{liveSession?.state?.pause_reason || 'tidak ada'}</strong></div>
          <div class="summary-row"><span>Produk sesi</span><strong>{liveSession?.products?.length || 0}</strong></div>
        </div>
        <div class="button-stack">
          <button class="btn btn-start" onclick={handleStartSession} disabled={Boolean(liveSession?.session)}>Mulai Sesi Live</button>
          <button class="btn btn-stop" onclick={() => handleAction('live_session.stop', stopLiveSession, 'Sesi live dihentikan.')} disabled={!liveSession?.session}>Stop Sesi</button>
          <button class="btn btn-ghost" onclick={handlePauseSession} disabled={!liveSession?.session}>Pause Q&amp;A</button>
          <button class="btn btn-ghost" onclick={() => handleAction('live_session.resume', resumeLiveSession, 'Rotasi dilanjutkan.')} disabled={!liveSession?.session}>Resume Rotasi</button>
          {#if status.emergency_stopped}
            <button class="btn btn-reset" onclick={() => handleAction('emergency.reset', emergencyReset, 'Emergency reset')}>Reset Emergency</button>
          {:else}
            <button class="btn btn-emergency" onclick={() => handleAction('emergency.stop', emergencyStop, 'Emergency stop activated')}>Emergency Stop</button>
          {/if}
        </div>
      </section>
    </div>

    <section class="card">
      <div class="section-title">Pipeline state machine</div>
      <div class="stepper">
        {#each pipelineTargets() as target, index}
          <button
            class="step"
            class:active={pipelineStateLabel() === target}
            disabled={pipelineStateLabel() === target}
            onclick={() => handleAction('pipeline.transition', () => pipelineTransition(target), `Pipeline berpindah ke ${target}`)}
          >
            <span class="step-index">{index + 1}</span>
            <span class="step-label">{target}</span>
          </button>
        {/each}
      </div>
    </section>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
  .panel-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .hero-grid, .section-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .hero-grid { margin-bottom: 14px; }
  .hero-card, .card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 18px; }
  .hero-card.alert { box-shadow: inset 0 0 0 1px rgba(233, 69, 96, 0.28); }
  .eyebrow, .section-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.1px; }
  .hero-value { font-size: 32px; font-weight: 900; margin: 8px 0; }
  .hero-copy, .muted { color: var(--muted); font-size: 13px; }
  .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 12px; }
  .form-group { display: flex; flex-direction: column; gap: 6px; }
  .form-group label { font-size: 12px; font-weight: 700; color: var(--text); }
  .form-input { padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--rsm); background: rgba(255, 255, 255, 0.03); color: var(--text); font-family: inherit; font-size: 14px; }
  .rtmp-actions, .button-stack, .target-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 14px; }
  .btn { padding: 10px 14px; border-radius: var(--rsm); border: 1px solid var(--border); cursor: pointer; font-weight: 700; font-family: inherit; }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; }
  .btn-ghost { background: rgba(255, 255, 255, 0.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-switch, .btn-start { background: rgba(34, 211, 238, 0.85); color: #04111f; border: none; }
  .btn-stop { background: rgba(255, 214, 0, 0.88); color: #161102; }
  .btn-emergency { background: rgba(233, 69, 96, 0.9); color: #fff; }
  .btn-reset { background: rgba(0, 230, 118, 0.88); color: #06150d; }
  .target-list { display: grid; gap: 10px; margin-top: 12px; }
  .target-item { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 12px; background: rgba(255,255,255,.02); border-radius: 8px; border: 1px solid rgba(255,255,255,.05); }
  .target-copy { flex: 1; min-width: 0; }
  .target-title { font-size: 14px; font-weight: 800; margin-bottom: 4px; }
  .target-meta { font-size: 12px; color: var(--muted); }
  .summary-list { display: grid; gap: 8px; margin-top: 12px; }
  .summary-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; }
  .result-box { margin-top: 12px; padding: 12px; border-radius: var(--rsm); }
  .result-box.pass { background: rgba(0, 230, 118, 0.05); }
  .result-box.fail { background: rgba(233, 69, 96, 0.05); }
  .check-row { display: flex; gap: 8px; font-size: 12px; padding-top: 8px; }
  .stepper { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-top: 12px; }
  .step { display: grid; gap: 8px; padding: 14px; border-radius: var(--radius); border: 1px solid var(--border); background: rgba(255, 255, 255, 0.04); color: var(--text); font-family: inherit; cursor: pointer; text-align: left; }
  .step.active { border-color: rgba(34, 211, 238, 0.5); background: rgba(34, 211, 238, 0.08); }
  .step:disabled { opacity: 1; cursor: default; }
  .step-index { width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.08); font-size: 12px; font-weight: 800; }
  .step-label { font-size: 14px; font-weight: 800; letter-spacing: 0.4px; }
</style>
