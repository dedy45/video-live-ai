<script lang="ts">
  import { onMount } from 'svelte';
  import { getRuntimeTruth } from '../../lib/api';
  import type { RuntimeTruth } from '../../lib/types';

  let truth: RuntimeTruth | null = $state(null);
  let error: string | null = $state(null);

  onMount(async () => {
    try {
      truth = await getRuntimeTruth() as RuntimeTruth;
    } catch (e: any) {
      error = e.message || 'Failed to load runtime truth';
    }
  });

  const modeBadgeClass = $derived(
    truth?.mock_mode ? 'badge badge-mock' : 'badge badge-live'
  );

  const modeLabel = $derived(
    truth?.mock_mode ? 'MOCK' : 'LIVE'
  );

  const validationClass = $derived(() => {
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

  const dataOriginLabel = $derived(() => {
    if (!truth?.provenance) return 'unknown';
    const values = Object.values(truth.provenance);
    if (values.every(v => v === 'mock')) return 'mock';
    if (values.some(v => v === 'real_live')) return 'real_live';
    if (values.some(v => v === 'real_local')) return 'real_local';
    if (values.every(v => v === 'derived')) return 'derived';
    return 'mixed';
  });

  const dataOriginClass = $derived(() => {
    const origin = dataOriginLabel();
    switch (origin) {
      case 'mock': return 'origin-mock';
      case 'real_local': return 'origin-real-local';
      case 'real_live': return 'origin-real-live';
      case 'derived': return 'origin-derived';
      default: return 'origin-unknown';
    }
  });

  const lastValidatedDisplay = $derived(() => {
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
    <span class={modeBadgeClass}>{modeLabel}</span>
    <span class="truth-item">
      <span class="truth-label">Validation:</span>
      <span class="truth-value {validationClass()}">{truth.validation_state}</span>
    </span>
    <span class="truth-item">
      <span class="truth-label">Origin:</span>
      <span class="truth-value {dataOriginClass()}" data-testid="truth-origin">{dataOriginLabel()}</span>
    </span>
    <span class="truth-item">
      <span class="truth-label">Validated:</span>
      <span class="truth-value" data-testid="truth-last-validated">{lastValidatedDisplay()}</span>
    </span>
    <span class="truth-sep">|</span>
    <span class="truth-item">
      <span class="truth-label">Face:</span>
      <span class="truth-value">{truth.face_runtime_mode}</span>
    </span>
    <span class="truth-item">
      <span class="truth-label">Voice:</span>
      <span class="truth-value">{truth.voice_runtime_mode}</span>
    </span>
    <span class="truth-item">
      <span class="truth-label">Stream:</span>
      <span class="truth-value">{truth.stream_runtime_mode}</span>
    </span>
  {:else if error}
    <span class="badge badge-error">ERROR</span>
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
  .badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    flex-shrink: 0;
  }
  .badge-mock {
    background: var(--yellow, #f59e0b);
    color: #000;
  }
  .badge-live {
    background: var(--green, #10b981);
    color: #fff;
  }
  .badge-error {
    background: var(--red, #ef4444);
    color: #fff;
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
  .validation-passed { color: var(--green, #10b981); }
  .validation-partial { color: var(--yellow, #f59e0b); }
  .validation-failed { color: var(--red, #ef4444); }
  .validation-blocked { color: var(--red, #ef4444); }
  .validation-validating { color: var(--blue, #3b82f6); }
  .validation-unvalidated { color: var(--text-secondary, #888); }
  .validation-unknown { color: var(--red, #ef4444); }
  .origin-mock { color: var(--yellow, #f59e0b); }
  .origin-real-local { color: var(--green, #10b981); }
  .origin-real-live { color: #22d3ee; }
  .origin-derived { color: var(--text-secondary, #888); }
  .origin-unknown { color: var(--red, #ef4444); }
</style>
