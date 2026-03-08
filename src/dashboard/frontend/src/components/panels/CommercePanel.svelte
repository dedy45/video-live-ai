<script lang="ts">
  import { onMount } from 'svelte';
  import { getProducts, getRevenue, switchProduct } from '../../lib/api';
  import ProvenanceBadge from '../common/ProvenanceBadge.svelte';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let products = $state<any[]>([]);
  let revenue = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);

  onMount(async () => {
    try {
      const [p, r] = await Promise.all([getProducts(), getRevenue()]);
      products = p;
      revenue = r;
    } catch (e: any) {
      error = e.message;
    }
    loading = false;
  });

  async function handleSwitchProduct(productId: number, productName: string) {
    receipt = null;
    try {
      const result = await switchProduct(productId);
      receipt = { action: 'product.switch', status: 'success', message: `Switched to ${result.product || productName}`, timestamp: Date.now() };
    } catch (e: any) {
      receipt = { action: 'product.switch', status: 'error', message: e.message, timestamp: Date.now() };
    }
  }
</script>

<div class="panel">
  <div class="panel-header">
    <h2 class="panel-title">Commerce</h2>
    <ProvenanceBadge provenance="derived" />
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="grid">
      <div class="card">
        <div class="card-title">Revenue Summary</div>
        <div class="metric-value">Rp {(revenue.total || 0).toLocaleString()}</div>
      </div>
      <div class="card">
        <div class="card-title">Products ({products.length})</div>
        {#each products as product}
          <div class="product-row">
            <span>{product.name}</span>
            <span class="product-right">
              <span class="muted">{product.price_formatted}</span>
              <button class="btn btn-ghost btn-xs" onclick={() => handleSwitchProduct(product.id, product.name)}>Switch</button>
            </span>
          </div>
        {/each}
        {#if products.length === 0}
          <p class="muted">No products loaded</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .panel-title { font-size: 18px; font-weight: 700; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 14px; }
  .card { background: var(--card); border-radius: var(--radius); padding: 18px; border: 1px solid var(--border); }
  .card-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 10px; }
  .metric-value { font-size: 22px; font-weight: 800; }
  .product-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 13px; border-bottom: 1px solid var(--border); }
  .product-right { display: flex; align-items: center; gap: 8px; }
  .btn { border: none; border-radius: var(--rsm); cursor: pointer; font-size: 12px; font-weight: 700; font-family: inherit; transition: all .2s; }
  .btn-ghost { background: rgba(255,255,255,.06); color: var(--text); border: 1px solid var(--border); }
  .btn-xs { padding: 2px 6px; font-size: 10px; }
  .muted { color: var(--muted); }
  .error { color: var(--accent); }
</style>
