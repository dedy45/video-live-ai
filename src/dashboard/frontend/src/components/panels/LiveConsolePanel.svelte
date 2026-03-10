<script lang="ts">
  import { onMount } from 'svelte';
  import { getStatus, getOpsSummary } from '../../lib/api';
  import { useDashboardRealtime } from '../../lib/stores/dashboard.svelte';
  import type { RealtimeSnapshot } from '../../lib/realtime';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';

  const rt = useDashboardRealtime();

  let status = $state<Record<string, any>>({});
  let opsSummary = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');

  function handleSnapshot(snapshot: RealtimeSnapshot) {
    status = {
      ...status,
      state: snapshot.pipeline_state || status.state,
      stream_running: snapshot.stream_running,
      emergency_stopped: snapshot.emergency_stopped,
      mock_mode: snapshot.mock_mode,
      current_product: snapshot.current_product,
    };
  }

  $effect(() => {
    if (rt.snapshot) {
      handleSnapshot(rt.snapshot);
    }
  });

  onMount(async () => {
    try {
      const [s, ops] = await Promise.all([getStatus(), getOpsSummary()]);
      status = s;
      opsSummary = ops;
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  const currentProduct = $derived(status.current_product || null);
  const operatorAlert = $derived(opsSummary.overall_status || 'unknown');
</script>

<div class="live-console-panel">
  <div class="panel-header">
    <h2 class="panel-title">Live Console</h2>
    <ProvenanceBadge source="realtime" />
  </div>

  {#if loading}
    <div class="loading">Loading live console...</div>
  {:else if error}
    <div class="error">Error: {error}</div>
  {:else}
    <div class="console-grid">
      <!-- Current Product Section -->
      <section class="console-section current-product">
        <h3>Current Product</h3>
        {#if currentProduct}
          <div class="product-card">
            <div class="product-name">{currentProduct.name || 'Unknown Product'}</div>
            <div class="product-price">{currentProduct.price_formatted || 'N/A'}</div>
          </div>
        {:else}
          <div class="empty-state">No active product</div>
        {/if}
      </section>

      <!-- Operator Alert Section -->
      <section class="console-section operator-alert">
        <h3>Operator Alert</h3>
        <div class="alert-badge status-{operatorAlert}">
          {operatorAlert.toUpperCase()}
        </div>
      </section>

      <!-- Script Rail Section -->
      <section class="console-section script-rail">
        <h3>Script Rail</h3>
        <div class="placeholder">
          <p>Opening hook, pitch block, proof/benefit line</p>
          <p class="note">Script assistance coming in next phase</p>
        </div>
      </section>

      <!-- Next Best Action Section -->
      <section class="console-section next-action">
        <h3>Next Best Action</h3>
        <div class="placeholder">
          <p>Guidance: what to say next, what to check next</p>
          <p class="note">Action rail coming in next phase</p>
        </div>
      </section>

      <!-- Quick Actions Section -->
      <section class="console-section quick-actions">
        <h3>Quick Actions</h3>
        <div class="action-buttons">
          <button class="action-btn" disabled>Voice Test</button>
          <button class="action-btn" disabled>Switch Product</button>
          <button class="action-btn" disabled>Run Validation</button>
        </div>
        <p class="note">Quick actions wired in next phases</p>
      </section>
    </div>
  {/if}
</div>

<style>
  .live-console-panel {
    background: var(--panel-bg);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .panel-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 0;
    color: var(--text-primary);
  }

  .loading,
  .error {
    padding: 20px;
    text-align: center;
    color: var(--text-secondary);
  }

  .error {
    color: var(--error-color);
  }

  .console-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 16px;
  }

  .console-section {
    background: var(--section-bg);
    border-radius: 6px;
    padding: 16px;
    border: 1px solid var(--border-color);
  }

  .console-section h3 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 12px 0;
    color: var(--text-primary);
  }

  .product-card {
    padding: 12px;
    background: var(--card-bg);
    border-radius: 4px;
  }

  .product-name {
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--text-primary);
  }

  .product-price {
    color: var(--accent-color);
    font-size: 1.1rem;
  }

  .empty-state {
    color: var(--text-secondary);
    font-style: italic;
  }

  .alert-badge {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.9rem;
  }

  .alert-badge.status-ready {
    background: var(--success-bg);
    color: var(--success-color);
  }

  .alert-badge.status-degraded {
    background: var(--warning-bg);
    color: var(--warning-color);
  }

  .alert-badge.status-unknown {
    background: var(--neutral-bg);
    color: var(--text-secondary);
  }

  .placeholder {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .placeholder p {
    margin: 8px 0;
  }

  .note {
    font-size: 0.85rem;
    color: var(--text-tertiary);
    font-style: italic;
  }

  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 8px;
  }

  .action-btn {
    padding: 10px 16px;
    background: var(--button-bg);
    color: var(--button-text);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s;
  }

  .action-btn:hover:not(:disabled) {
    background: var(--button-hover-bg);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
