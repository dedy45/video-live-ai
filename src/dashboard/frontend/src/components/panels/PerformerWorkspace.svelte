<script lang="ts">
  import { onMount } from 'svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import VoicePanel from './VoicePanel.svelte';
  import EnginePanel from './EnginePanel.svelte';
  import PerformerPreviewPanel from './PerformerPreviewPanel.svelte';
  import PerformerValidationPanel from './PerformerValidationPanel.svelte';
  import PerformerTechnicalPanel from './PerformerTechnicalPanel.svelte';
  import {
    getLiveTalkingConfig,
    getLiveTalkingDebugTargets,
    getLiveTalkingLogs,
    getLiveTalkingStatus,
    getReadiness,
    getRuntimeTruth,
    startLiveTalking,
    stopLiveTalking,
    validateAudioChunkingSmoke,
    validateLiveTalkingEngine,
    validateRealModeReadiness,
    validateRuntimeTruth,
    validateVoiceLocalClone,
    voiceQueueClear,
    voiceRestart,
    voiceTestSpeak,
    voiceWarmup,
  } from '../../lib/api';
  import { buildReceipt, runOperatorAction, runReconciledEngineAction } from '../../lib/performer-actions';
  import { bootstrapRuntimeSnapshot } from '../../lib/runtime-client';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import type {
    EngineConfig,
    EngineStatus,
    LiveTalkingDebugTargets,
    PerformerValidationCheckId,
    PerformerValidationEntry,
    ReadinessResult,
    RuntimeTruth,
    ValidationResult,
    VoiceTestSpeakResult,
  } from '../../lib/types';

  type TabId = 'ringkasan' | 'suara' | 'avatar' | 'preview' | 'validasi' | 'teknis';

  const tabs: Array<{ id: TabId; label: string }> = [
    { id: 'ringkasan', label: 'Ringkasan' },
    { id: 'suara', label: 'Suara' },
    { id: 'avatar', label: 'Avatar' },
    { id: 'preview', label: 'Preview' },
    { id: 'validasi', label: 'Validasi' },
    { id: 'teknis', label: 'Teknis' },
  ];

  let activeTab = $state<TabId>('ringkasan');
  let truth = $state<RuntimeTruth | null>(null);
  let readiness = $state<ReadinessResult | null>(null);
  let config = $state<EngineConfig | null>(null);
  let engineStatus = $state<EngineStatus | null>(null);
  let engineLogs = $state<string[]>([]);
  let debugTargets = $state<LiveTalkingDebugTargets | null>(null);
  let voiceTestResult = $state<VoiceTestSpeakResult | null>(null);
  let validationResults = $state<Partial<Record<PerformerValidationCheckId, PerformerValidationEntry>>>({});
  let receipt = $state<ReceiptType | null>(null);
  let loading = $state(true);
  let error = $state('');
  let previewLoading = $state(false);
  let technicalLoading = $state(false);
  let technicalError = $state('');
  let busyAction = $state('');
  let runningCheck = $state('');
  let previewLoaded = $state(false);
  let technicalLoaded = $state(false);
  let engineLoaded = $state(false);

  const blockers = $derived(readiness?.blocking_issues || []);
  const faceState = $derived(truth?.face_engine?.engine_state || engineStatus?.state || 'unknown');
  const faceRunning = $derived(faceState === 'running');
  const voiceState = $derived.by(() => {
    const voice = truth?.voice_engine;
    if (!voice) return { label: 'Belum ada data', summary: 'Snapshot suara belum tersedia.' };
    if (voice.server_reachable && voice.reference_ready) {
      return { label: 'Siap', summary: 'Mesin suara terhubung dan referensi clone sudah siap.' };
    }
    if (!voice.server_reachable) {
      return { label: 'Tertahan', summary: 'Sidecar suara belum bisa dijangkau.' };
    }
    if (!voice.reference_ready) {
      return { label: 'Perlu referensi', summary: 'Referensi suara belum siap.' };
    }
    return { label: 'Belum aktif', summary: 'Status suara belum dapat dipastikan.' };
  });
  const previewHealthy = $derived(Boolean(debugTargets?.targets?.webrtcapi?.reachable));
  const previewState = $derived.by(() => {
    if (!debugTargets) {
      return {
        label: 'Belum dicek',
        summary: 'Preview vendor baru dicek saat tab Preview dibuka atau validasi preview dijalankan.',
      };
    }
    if (previewHealthy) {
      return {
        label: 'Siap',
        summary: 'Preview vendor bisa dijangkau.',
      };
    }
    return {
      label: 'Tertahan',
      summary: 'Preview vendor belum bisa dijangkau.',
    };
  });

  async function refreshTruth() {
    const snapshot = await bootstrapRuntimeSnapshot();
    truth = snapshot.truth as RuntimeTruth | null;
  }

  async function refreshReadiness() {
    readiness = await getReadiness();
  }

  async function refreshConfig() {
    config = await getLiveTalkingConfig();
  }

  async function refreshEngineStatus() {
    engineStatus = await getLiveTalkingStatus();
    engineLoaded = true;
  }

  async function refreshPreviewData() {
    previewLoading = true;
    try {
      const tasks: Array<Promise<unknown>> = [];

      if (!config) {
        tasks.push(
          getLiveTalkingConfig().then((nextConfig) => {
            config = nextConfig;
          }),
        );
      }

      tasks.push(
        getLiveTalkingDebugTargets().then((nextTargets) => {
          debugTargets = nextTargets;
        }),
      );

      await Promise.all(tasks);
      previewLoaded = true;
    } finally {
      previewLoading = false;
    }
  }

  async function refreshTechnical() {
    technicalLoading = true;
    technicalError = '';
    try {
      const [nextStatus, nextLogs] = await Promise.all([
        getLiveTalkingStatus(),
        getLiveTalkingLogs(50) as Promise<{ lines: string[]; count: number }>,
      ]);
      engineStatus = nextStatus;
      engineLogs = nextLogs.lines || [];
      engineLoaded = true;
      technicalLoaded = true;
    } catch (nextError: any) {
      technicalError = nextError?.message ?? 'Gagal memuat data teknis.';
    } finally {
      technicalLoading = false;
    }
  }

  async function refreshTechnicalPanelData() {
    const tasks: Array<Promise<unknown>> = [refreshTechnical()];

    if (!previewLoading) {
      tasks.push(refreshPreviewData());
    }

    await Promise.all(tasks);
  }

  async function refreshAll() {
    loading = true;
    error = '';
    try {
      const tasks: Array<Promise<unknown>> = [refreshTruth(), refreshReadiness()];

      if (engineLoaded || technicalLoaded || activeTab === 'avatar' || activeTab === 'teknis') {
        tasks.push(activeTab === 'teknis' || technicalLoaded ? refreshTechnicalPanelData() : refreshEngineStatus());
      }

      if (previewLoaded || activeTab === 'preview') {
        tasks.push(refreshPreviewData());
      }

      await Promise.all(tasks);
    } catch (nextError: any) {
      error = nextError?.message ?? 'Gagal memuat workspace Avatar & Suara.';
    } finally {
      loading = false;
    }
  }

  function setReceipt(nextReceipt: ReceiptType) {
    receipt = nextReceipt;
  }

  async function runBusy(action: string, work: () => Promise<void>) {
    busyAction = action;
    try {
      await work();
    } finally {
      busyAction = '';
    }
  }

  async function handleWarmup() {
    await runBusy('voice.warmup', async () => {
      try {
        await runOperatorAction({
          action: 'voice.warmup',
          title: 'Permintaan pemanasan suara dikirim',
          fallbackMessage: 'Pemanasan suara selesai.',
          execute: voiceWarmup,
          onReceipt: setReceipt,
        });
      } finally {
        await Promise.all([refreshTruth(), refreshReadiness()]);
      }
    });
  }

  async function handleRestart() {
    await runBusy('voice.restart', async () => {
      try {
        await runOperatorAction({
          action: 'voice.restart',
          title: 'Permintaan mulai ulang suara dikirim',
          fallbackMessage: 'Mesin suara diminta mulai ulang.',
          execute: voiceRestart,
          onReceipt: setReceipt,
        });
      } finally {
        await Promise.all([refreshTruth(), refreshReadiness()]);
      }
    });
  }

  async function handleClearQueue() {
    await runBusy('voice.queue.clear', async () => {
      try {
        await runOperatorAction({
          action: 'voice.queue.clear',
          title: 'Antrian suara diminta untuk dikosongkan',
          fallbackMessage: 'Antrian suara berhasil dibersihkan.',
          execute: voiceQueueClear,
          onReceipt: setReceipt,
        });
      } finally {
        await refreshTruth();
      }
    });
  }

  async function handleTestSpeak(text: string) {
    await runBusy('voice.test.speak', async () => {
      voiceTestResult = null;
      try {
        const result = await runOperatorAction({
          action: 'voice.test.speak',
          title: 'Tes suara selesai',
          pendingTitle: 'Tes suara sedang dijalankan',
          pendingMessage: 'Dashboard sedang menunggu hasil sintesis suara.',
          fallbackMessage: 'Tes suara selesai.',
          execute: () => voiceTestSpeak(text),
          onReceipt: setReceipt,
        }) as VoiceTestSpeakResult;
        voiceTestResult = result;
      } finally {
        await refreshTruth();
      }
    });
  }

  async function handleStartAvatar() {
    await runBusy('engine.start', async () => {
      await runReconciledEngineAction({
        action: 'engine.start',
        title: 'Avatar menerima perintah jalan',
        desiredState: 'running',
        execute: startLiveTalking,
        getTruth: getRuntimeTruth,
        getStatus: getLiveTalkingStatus,
        onReceipt: setReceipt,
        onTruthUpdate: (nextTruth) => {
          truth = nextTruth;
        },
        onStatusUpdate: (nextStatus) => {
          engineStatus = nextStatus;
          engineLoaded = true;
        },
      });
      const followUp: Array<Promise<unknown>> = [refreshReadiness(), refreshEngineStatus()];
      if (previewLoaded || activeTab === 'preview') followUp.push(refreshPreviewData());
      if (technicalLoaded || activeTab === 'teknis') followUp.push(refreshTechnical());
      await Promise.all(followUp);
    });
  }

  async function handleStopAvatar() {
    await runBusy('engine.stop', async () => {
      await runReconciledEngineAction({
        action: 'engine.stop',
        title: 'Avatar menerima perintah berhenti',
        desiredState: 'stopped',
        execute: stopLiveTalking,
        getTruth: getRuntimeTruth,
        getStatus: getLiveTalkingStatus,
        onReceipt: setReceipt,
        onTruthUpdate: (nextTruth) => {
          truth = nextTruth;
        },
        onStatusUpdate: (nextStatus) => {
          engineStatus = nextStatus;
          engineLoaded = true;
        },
      });
      const followUp: Array<Promise<unknown>> = [refreshReadiness(), refreshEngineStatus()];
      if (previewLoaded || activeTab === 'preview') followUp.push(refreshPreviewData());
      if (technicalLoaded || activeTab === 'teknis') followUp.push(refreshTechnical());
      await Promise.all(followUp);
    });
  }

  async function handleTabChange(nextTab: TabId) {
    activeTab = nextTab;

    if (nextTab === 'avatar' && !engineLoaded && !technicalLoading) {
      await refreshEngineStatus();
      return;
    }

    if (nextTab === 'preview' && !previewLoaded && !previewLoading) {
      await refreshPreviewData();
      return;
    }

    if (nextTab === 'teknis' && !technicalLoaded && !technicalLoading) {
      await refreshTechnicalPanelData();
    }
  }

  function validationSummary(result: ValidationResult, label: string): PerformerValidationEntry {
    const failedChecks = (result.checks || []).filter((check) => !check.passed);
    const status = result.status === 'pass' ? 'pass' : result.status === 'blocked' ? 'blocked' : result.status === 'error' ? 'error' : 'fail';
    return {
      label,
      status,
      timestamp: new Date().toISOString(),
      summary:
        status === 'pass'
          ? `${label} lulus.`
          : failedChecks[0]?.message || result.blockers?.[0] || result.error || `${label} perlu perhatian.`,
      details: failedChecks.map((check) => `${check.check}: ${check.message}`),
    };
  }

  async function handleRunCheck(checkId: PerformerValidationCheckId) {
    const labels: Record<PerformerValidationCheckId, string> = {
      runtime_truth: 'Runtime Truth',
      engine: 'Engine Avatar',
      voice_clone: 'Clone Suara Lokal',
      audio_chunking: 'Chunking Audio',
      real_mode: 'Kesiapan Runtime',
      preview_targets: 'Target Preview',
    };

    runningCheck = checkId;
    validationResults = {
      ...validationResults,
      [checkId]: {
        label: labels[checkId],
        status: 'pending',
        summary: 'Pemeriksaan sedang dijalankan.',
        timestamp: new Date().toISOString(),
      },
    };

    try {
      if (checkId === 'preview_targets') {
        const targets = await getLiveTalkingDebugTargets();
        debugTargets = targets;
        const allReachable = Object.values(targets.targets).every((target) => target.reachable);
        validationResults = {
          ...validationResults,
          preview_targets: {
            label: labels.preview_targets,
            status: allReachable ? 'pass' : 'fail',
            summary: allReachable
              ? 'Semua target preview dapat dijangkau.'
              : 'Preview vendor belum bisa dijangkau.',
            timestamp: new Date().toISOString(),
            details: Object.entries(targets.targets)
              .filter(([, target]) => !target.reachable)
              .map(([key, target]) => `${key}: ${target.error || 'Tidak terjangkau'}`),
          },
        };
        receipt = buildReceipt({
          action: 'preview.targets.validate',
          title: 'Pemeriksaan target preview selesai',
          status: allReachable ? 'success' : 'warning',
          message: allReachable
            ? 'Semua target preview merespons normal.'
            : 'Sebagian target preview belum bisa dijangkau.',
        });
        return;
      }

      const runners: Record<Exclude<PerformerValidationCheckId, 'preview_targets'>, () => Promise<ValidationResult>> = {
        runtime_truth: validateRuntimeTruth,
        engine: validateLiveTalkingEngine,
        voice_clone: validateVoiceLocalClone,
        audio_chunking: validateAudioChunkingSmoke,
        real_mode: validateRealModeReadiness,
      };

      const result = await runners[checkId as Exclude<PerformerValidationCheckId, 'preview_targets'>]();
      const summary = validationSummary(result, labels[checkId]);
      validationResults = { ...validationResults, [checkId]: summary };
      receipt = buildReceipt({
        action: `validation.${checkId}`,
        title: `${labels[checkId]} selesai diperiksa`,
        status: summary.status === 'pass' ? 'success' : summary.status === 'blocked' ? 'blocked' : summary.status === 'error' ? 'error' : 'warning',
        message: summary.summary,
        details: summary.details,
      });
    } catch (nextError: any) {
      validationResults = {
        ...validationResults,
        [checkId]: {
          label: labels[checkId],
          status: 'error',
          summary: nextError?.message ?? 'Pemeriksaan gagal dijalankan.',
          timestamp: new Date().toISOString(),
        },
      };
      receipt = buildReceipt({
        action: `validation.${checkId}`,
        title: `${labels[checkId]} gagal diperiksa`,
        status: 'error',
        message: nextError?.message ?? 'Pemeriksaan gagal dijalankan.',
      });
    } finally {
      runningCheck = '';
    }
  }

  onMount(() => {
    void refreshAll();
  });
</script>

<section class="workspace" data-testid="performer-panel">
  <div class="workspace-topbar">
    <div class="tabs" role="tablist" aria-label="Avatar dan suara workspace">
      {#each tabs as tab}
        <button
          class="tab-button"
          class:is-active={activeTab === tab.id}
          type="button"
          onclick={() => void handleTabChange(tab.id)}
        >
          {tab.label}
        </button>
      {/each}
    </div>
    <button class="refresh-button" type="button" onclick={refreshAll} disabled={loading || busyAction !== ''}>
      Muat Ulang Status Langsung
    </button>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <div class="state-card">
      <p>Memuat workspace Avatar & Suara...</p>
    </div>
  {:else if error}
    <div class="state-card error-state">
      <p>{error}</p>
    </div>
  {:else}
    {#if activeTab === 'ringkasan'}
      <section class="summary-grid">
        <article class="summary-card">
          <span class="eyebrow">Host</span>
          <strong>{truth?.host?.name || 'Belum diketahui'}</strong>
          <p>Role {truth?.host?.role || 'unknown'} · Deploy {truth?.deployment_mode || 'unknown'}</p>
        </article>
        <article class="summary-card">
          <span class="eyebrow">Suara</span>
          <strong>{voiceState.label}</strong>
          <p>{voiceState.summary}</p>
        </article>
        <article class="summary-card">
          <span class="eyebrow">Avatar</span>
          <strong>{faceRunning ? 'Berjalan' : 'Berhenti'}</strong>
          <p>Model {truth?.face_engine?.resolved_model || engineStatus?.resolved_model || 'unknown'}</p>
        </article>
        <article class="summary-card">
          <span class="eyebrow">Preview</span>
          <strong>{previewState.label}</strong>
          <p>{previewState.summary}</p>
        </article>
      </section>

      {#if blockers.length > 0}
        <div class="warning-banner">
          Kesiapan runtime tertahan: {blockers.join(', ')}.
          {#if readiness?.recommended_next_action}
            <span> Langkah berikutnya: {readiness.recommended_next_action}</span>
          {/if}
        </div>
      {/if}

      <section class="action-grid">
        <article class="card">
          <h2>Kontrol Cepat</h2>
          <div class="button-stack">
            <button class="btn btn-primary" type="button" onclick={handleWarmup} disabled={busyAction !== ''}>
              Panaskan Mesin Suara
            </button>
            {#if faceRunning}
              <button class="btn btn-warning" type="button" onclick={handleStopAvatar} disabled={busyAction !== ''}>
                Hentikan Avatar
              </button>
            {:else}
              <button class="btn btn-primary" type="button" onclick={handleStartAvatar} disabled={busyAction !== ''}>
                Jalankan Avatar
              </button>
            {/if}
            <button class="btn btn-secondary" type="button" onclick={() => handleRunCheck('real_mode')} disabled={runningCheck !== ''}>
              Cek Kesiapan Runtime
            </button>
          </div>
        </article>

        <article class="card">
          <h2>Snapshot Operator</h2>
          <div class="metric-list">
            <div><span>Status validasi</span><strong>{truth?.validation_state || 'Belum ada'}</strong></div>
            <div><span>Insiden terbuka</span><strong>{truth?.incident_summary?.open_count ?? 0}</strong></div>
            <div><span>Guardrail restart storm</span><strong>{truth?.guardrails?.restart_storm ? 'Aktif' : 'Tidak'}</strong></div>
            <div><span>Guardrail disk pressure</span><strong>{truth?.guardrails?.disk_pressure ? 'Aktif' : 'Tidak'}</strong></div>
          </div>
        </article>
      </section>
    {:else if activeTab === 'suara'}
      <VoicePanel
        {truth}
        {busyAction}
        {voiceTestResult}
        onWarmup={handleWarmup}
        onRestart={handleRestart}
        onClearQueue={handleClearQueue}
        onTestSpeak={handleTestSpeak}
      />
    {:else if activeTab === 'avatar'}
      <EnginePanel
        {truth}
        {engineStatus}
        {busyAction}
        onStart={handleStartAvatar}
        onStop={handleStopAvatar}
        onValidate={() => handleRunCheck('engine')}
      />
    {:else if activeTab === 'preview'}
      <PerformerPreviewPanel
        loading={previewLoading}
        checkedAt={debugTargets?.checked_at || null}
        targets={debugTargets?.targets || null}
        onRefresh={refreshPreviewData}
      />
    {:else if activeTab === 'validasi'}
      <PerformerValidationPanel
        {runningCheck}
        results={validationResults}
        onRunCheck={handleRunCheck}
      />
    {:else if activeTab === 'teknis'}
      <PerformerTechnicalPanel
        {truth}
        {config}
        {engineStatus}
        {engineLogs}
        {debugTargets}
        loading={technicalLoading}
        error={technicalError}
        onRefresh={refreshTechnicalPanelData}
      />
    {/if}
  {/if}
</section>

<style>
  .workspace {
    display: grid;
    gap: 18px;
  }

  .workspace-topbar {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
  }

  .tabs {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .tab-button,
  .refresh-button,
  .btn {
    border-radius: 999px;
    border: 1px solid var(--border);
    padding: 10px 14px;
    font: inherit;
    font-weight: 700;
    cursor: pointer;
  }

  .tab-button,
  .refresh-button,
  .btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text);
  }

  .tab-button.is-active {
    background: var(--accent);
    color: #111827;
    border-color: transparent;
  }

  .refresh-button:disabled,
  .btn:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .summary-grid,
  .action-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 14px;
  }

  .summary-card,
  .card,
  .state-card {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--card);
    padding: 18px;
  }

  .summary-card strong {
    display: block;
    font-size: 24px;
    color: var(--text);
  }

  .summary-card p,
  .state-card p {
    margin: 6px 0 0;
    color: var(--muted);
    line-height: 1.5;
  }

  .eyebrow {
    display: block;
    margin-bottom: 8px;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
  }

  .warning-banner {
    border-radius: 16px;
    border: 1px solid rgba(245, 158, 11, 0.35);
    background: rgba(245, 158, 11, 0.12);
    color: #fcd34d;
    padding: 14px 16px;
    line-height: 1.5;
  }

  .card {
    display: grid;
    gap: 14px;
  }

  .card h2 {
    margin: 0;
    color: var(--text);
    font-size: 18px;
  }

  .button-stack,
  .metric-list {
    display: grid;
    gap: 10px;
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

  .error-state {
    border-color: rgba(239, 68, 68, 0.4);
    background: rgba(239, 68, 68, 0.12);
  }

  .btn-primary {
    background: var(--accent);
    color: #111827;
  }

  .btn-warning {
    background: #f59e0b;
    color: #111827;
  }

  @media (max-width: 720px) {
    .workspace-topbar {
      align-items: stretch;
    }
  }
</style>
