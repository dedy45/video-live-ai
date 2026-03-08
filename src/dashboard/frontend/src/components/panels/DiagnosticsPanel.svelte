<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { getHealthSummary, getBrainStats, getBrainHealth, brainTest, validateMockStack } from '../../lib/api';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  const rt = useDashboardRealtime();

  let health = $state<Record<string, any>>({});
  let brainStats = $state<Record<string, any>>({});
  let brainHealth = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);
  let brainTestResult = $state<Record<string, any> | null>(null);

  $effect(() => {
    if (rt.snapshot) {
      if (rt.snapshot.components) {
        const previousHealth = untrack(() => health);
        health = { ...previousHealth, components: rt.snapshot.components };
      }
      if (rt.snapshot.llm_stats) {
        const previousBrainStats = untrack(() => brainStats);
        brainStats = { ...previousBrainStats, ...rt.snapshot.llm_stats };
      }
    }
  });

  onMount(async () => {
    try {
      const [h, bs, bh] = await Promise.all([
        getHealthSummary(),
        getBrainStats(),
        getBrainHealth(),
      ]);
      health = h;
      brainStats = bs;
      brainHealth = bh;
    } catch (e: any) {
      error = e.message;
    }
    loading = false;
    rt.start();
  });

  onDestroy(() => {
    rt.stop();
  });

  async function handleBrainTest() {
    receipt = null;
    brainTestResult = null;
    try {
      brainTestResult = await brainTest({ user_prompt: 'Halo, perkenalkan produk ini!' });
      receipt = {
        action: 'brain.test',
        status: brainTestResult.success ? 'success' : 'error',
        message: brainTestResult.success
          ? `${brainTestResult.provider}/${brainTestResult.model} — ${brainTestResult.latency_ms}ms`
          : brainTestResult.error || 'Brain test failed',
        timestamp: Date.now(),
      };
    } catch (e: any) {
      receipt = { action: 'brain.test', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }

  async function handleValidateMockStack() {
    receipt = null;
    try {
      const result = await validateMockStack();
      receipt = {
        action: 'validate.mock-stack',
        status: result.status === 'pass' ? 'success' : 'error',
        message: `Mock stack: ${result.status} (${(result.checks || []).length} checks)`,
        timestamp: Date.now(),
      };
    } catch (e: any) {
      receipt = { action: 'validate.mock-stack', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Diagnostics</h2>
    <ProvenanceBadge provenance={rt.snapshot?.truth?.provenance?.system_status || (health.mock_mode ? 'mock' : 'real_local')} />
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading diagnostics...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <div class="card">
        <div class="card-title">System Health: {health.status || 'unknown'}</div>
        {#each Object.entries(health.components || {}) as [name, status]}
          <div class="diag-row">
            <span class:green={status === 'healthy' || status === 'mock'}
                  class:red={status === 'failed'}
                  class:yellow={status === 'degraded'}>●</span>
            <span>{name}</span>
            <span class="muted">{status}</span>
          </div>
        {/each}
      </div>

      <div class="card">
        <div class="card-title">LLM Brain Health</div>
        <p class="muted">Healthy: {brainHealth.healthy_count || 0} / {brainHealth.total_count || 0}</p>
        {#each Object.entries(brainHealth.providers || {}) as [name, ok]}
          <div class="diag-row">
            <span class:green={ok} class:red={!ok}>●</span>
            <span>{name}</span>
            <span class="muted">{ok ? 'healthy' : 'failed'}</span>
          </div>
        {/each}
      </div>

      <div class="card">
        <div class="card-title">LLM Adapters</div>
        {#each Object.entries(brainStats.adapters || {}) as [name, info]}
          <div class="diag-row">
            <span class:green={info.available} class:red={!info.available}>●</span>
            <span>{name}</span>
            <span class="muted">{info.model || 'unknown'}</span>
          </div>
        {/each}
      </div>
    </div>

    <div class="card" style="margin-top: 14px;">
      <div class="card-title">Operator Actions</div>
      <div class="btn-row">
        <button class="btn btn-ghost btn-sm" onclick={handleBrainTest}>Test Brain</button>
        <button class="btn btn-ghost btn-sm" onclick={handleValidateMockStack}>Validate Mock Stack</button>
        <a href="/docs" target="_blank" class="btn btn-ghost btn-sm">API Docs</a>
        <a href="/diagnostic/" target="_blank" class="btn btn-ghost btn-sm">System Diagnostic</a>
      </div>
    </div>

    {#if brainTestResult}
      <div class="card" style="margin-top: 10px;">
        <div class="card-title">Brain Test Result</div>
        <div class="diag-row">
          <span class:green={brainTestResult.success} class:red={!brainTestResult.success}>●</span>
          <span>{brainTestResult.provider}/{brainTestResult.model}</span>
          <span class="muted">{brainTestResult.latency_ms}ms</span>
        </div>
        {#if brainTestResult.text}
          <p class="brain-output">{brainTestResult.text.slice(0, 300)}</p>
        {/if}
        {#if brainTestResult.error}
          <p class="error">{brainTestResult.error}</p>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px; }
  .diag-row { display: flex; gap: 8px; font-size: 13px; padding: 4px 0; align-items: center; }
  .green { color: var(--green); }
  .red { color: var(--accent); }
  .yellow { color: var(--yellow); }
  .btn-row { display: flex; gap: 8px; flex-wrap: wrap; }
  .btn { padding: 8px 16px; border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; text-decoration: none; display: inline-flex; align-items: center; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-sm { padding: 5px 10px; font-size: 11px; }
  .brain-output { font-size: 12px; color: var(--text); padding: 8px; background: rgba(0,0,0,.2); border-radius: var(--rsm); margin-top: 8px; white-space: pre-wrap; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
