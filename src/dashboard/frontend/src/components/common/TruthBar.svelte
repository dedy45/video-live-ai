<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import StatusBadge from './StatusBadge.svelte';
  import type { RuntimeTruth, StatusType } from '../../lib/types';

  const rt = useDashboardRealtime();

  let truth: RuntimeTruth | null = $state(null);
  let error: string | null = $state(null);
  let source: string = $state('');

  onMount(() => {
    rt.start();
  });

  onDestroy(() => {
    rt.stop();
  });

  // Sync truth from realtime store snapshot
  $effect(() => {
    const snap = rt.snapshot;
    if (snap?.truth) {
      truth = snap.truth as RuntimeTruth;
      source = snap.source;
      error = null;
    }
  });

  const modeStatus = $derived<StatusType>(
    truth?.mock_mode ? 'warning' : 'ready'
  );

  const validationStatus = $derived.by((): StatusType => {
    if (!truth) return 'idle';
    switch (truth.validation_state) {
      case 'passed': return 'ready';
      case 'partial': return 'warning';
      case 'failed': return 'error';
      case 'blocked': return 'error';
      case 'validating': return 'info';
      default: return 'idle';
    }
  });

  const validationClass = $derived.by(() => {
    if (!truth) return 'validation-unknown';
    switch (truth.validation_state) {
      case 'passed': return 'validation-passed';
      case 'partial': return 'validation-partial';
      case 'failed': return 'validation-failed';
      case 'blocked': return 'validation-blocked';
      case 'validating': return 'validation-validating';
      default: return 'validation-unvalidated';
    }
  });

  const dataOriginStatus = $derived.by((): StatusType => {
    if (!truth?.provenance) return 'idle';
    const values = Object.values(truth.provenance);
    if (values.every(v => v === 'mock')) return 'warning';
    if (values.some(v => v === 'real_live')) return 'ready';
    if (values.some(v => v === 'real_local')) return 'ready';
    if (values.every(v => v === 'derived')) return 'idle';
    return 'info';
  });

  const dataOriginLabel = $derived.by(() => {
    if (!truth?.provenance) return 'unknown';
    const values = Object.values(truth.provenance);
    if (values.every(v => v === 'mock')) return 'mock';
    if (values.some(v => v === 'real_live')) return 'real_live';
    if (values.some(v => v === 'real_local')) return 'real_local';
    if (values.every(v => v === 'derived')) return 'derived';
    return 'mixed';
  });

  const lastValidatedDisplay = $derived.by(() => {
    if (!truth) return 'never';
    if (!truth.last_validated_at) return 'never';
    try {
      const d = new Date(truth.last_validated_at);
      return d.toLocaleTimeString();
    } catch {
      return truth.last_validated_at;
    }
  });
</script>

<div class="truth-bar" data-testid="truth-bar">
  {#if truth}
    <StatusBadge status={modeStatus} label={truth.mock_mode ? 'MOCK' : 'LIVE'} size="sm" />
    <span class="truth-item">
      <span class="truth-label">Validation:</span>
      <StatusBadge status={validationStatus} label={truth.validation_state} size="sm" showDot={false} />
    </span>
    <span class="truth-item">
      <span class="truth-label">Origin:</span>
      <span class="test-hook" data-testid="truth-origin">{dataOriginLabel}</span>
      <StatusBadge status={dataOriginStatus} label={dataOriginLabel} size="sm" showDot={false} />
    </span>
    <span class="truth-item">
      <span class="truth-label">Validated:</span>
      <span class="truth-value" data-testid="truth-last-validated">{lastValidatedDisplay}</span>
    </span>
    {#if truth.host?.name}
      <span class="truth-item">
        <span class="truth-label">Host:</span>
        <span class="truth-value">{truth.host.name}</span>
      </span>
    {/if}
    {#if truth.host?.role}
      <span class="truth-item">
        <span class="truth-label">Role:</span>
        <span class="truth-value">{truth.host.role}</span>
      </span>
    {/if}
    {#if truth.deployment_mode}
      <span class="truth-item">
        <span class="truth-label">Deploy:</span>
        <StatusBadge status="info" label={truth.deployment_mode} size="sm" showDot={false} />
      </span>
    {/if}
    <span class="truth-sep">|</span>
    <span class="truth-item">
      <span class="truth-label">Face:</span>
      <span class="test-hook" data-testid="truth-face-mode">{truth.face_runtime_mode}</span>
      <StatusBadge status="info" label={truth.face_runtime_mode} size="sm" showDot={false} />
    </span>
    <span class="truth-item">
      <span class="truth-label">Voice:</span>
      <span class="test-hook" data-testid="truth-voice-mode">{truth.voice_runtime_mode}</span>
      <StatusBadge status="info" label={truth.voice_runtime_mode} size="sm" showDot={false} />
    </span>
    <span class="truth-item">
      <span class="truth-label">Stream:</span>
      <span class="test-hook" data-testid="truth-stream-mode">{truth.stream_runtime_mode}</span>
      <StatusBadge status="info" label={truth.stream_runtime_mode} size="sm" showDot={false} />
    </span>
    {#if source}
      <span class="truth-sep">|</span>
      <span class="truth-item">
        <span class="truth-label">Src:</span>
        <span class="truth-value truth-source" data-testid="truth-source">{source}</span>
      </span>
    {/if}
  {:else if error}
    <StatusBadge status="error" label="ERROR" size="sm" />
    <span class="truth-item truth-error">{error}</span>
  {:else}
    <span class="truth-item">Loading truth...</span>
  {/if}
</div>

<style>
  .truth-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 20px;
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid var(--border);
    font-size: 11px;
    font-family: monospace;
    overflow-x: auto;
  }
  .truth-sep {
    color: var(--text-secondary, #555);
    flex-shrink: 0;
  }
  .truth-item {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }
  .truth-label {
    color: var(--text-secondary, #888);
  }
  .truth-value {
    color: var(--text, #eee);
  }
  .truth-error {
    color: var(--red, #ef4444);
  }
  .truth-source {
    color: var(--text-secondary, #888);
    font-style: italic;
  }
  .test-hook {
    display: none;
  }
</style>
