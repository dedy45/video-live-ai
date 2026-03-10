<script lang="ts">
  import { onMount } from 'svelte';
  import { getProducts, getStatus, switchProduct } from '../../lib/api';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';

  let products = $state<any[]>([]);
  let currentProduct = $state<any>(null);
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);

  async function loadData() {
    loading = true;
    try {
      const [prods, status] = await Promise.all([getProducts(), getStatus()]);
      products = prods;
      currentProduct = status.current_product;
      error = '';
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function handleSwitchProduct(productId: number) {
    receipt = null;
    try {
      const result = await switchProduct(productId);
      receipt = {
        action: 'product.switch',
        status: 'success',
        message: `Switched to: ${result.product}`,
        timestamp: Date.now(),
      };
      await loadData();
    } catch (e: any) {
      receipt = {
        action: 'product.switch',
        status: 'error',
        message: e.message,
        timestamp: Date.now(),
      };
    }
  }

  onMount(loadData);

  const activeProduct = $derived(
    currentProduct ? products.find(p => p.id === currentProduct.id) : products[0]
  );
  const queuedProducts = $derived(
    products.filter(p => !currentProduct || p.id !== currentProduct.id)
  );
</script>

<div class="panel" data-testid="products-offers-panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Produk & Penawaran</h2>
      <p class="panel-subtitle">Katalog produk affiliate dengan poin penjualan, komisi, dan link platform.</p>
    </div>
    <button class="btn btn-ghost btn-sm" onclick={loadData}>Muat Ulang</button>
  </div>

  <ActionReceipt {receipt} />

  {#if loading}
    <p class="muted">Memuat produk...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="products-grid">
      <!-- Active Product Section -->
      <section class="product-card active">
        <div class="card-header">
          <h3 class="card-title">Produk Aktif</h3>
          <span class="badge badge-active">LIVE</span>
        </div>
        {#if activeProduct}
          <div class="product-info">
            <div class="product-name">{activeProduct.name}</div>
            <div class="product-price">{activeProduct.price_formatted}</div>
            <div class="product-category">{activeProduct.category}</div>
          </div>

          <div class="section">
            <h4 class="section-title">Komisi</h4>
            <div class="commission-rate">{activeProduct.commission_rate}%</div>
          </div>

          <div class="section">
            <h4 class="section-title">Link Affiliate</h4>
            <div class="links-list">
              {#each Object.entries(activeProduct.affiliate_links || {}) as [platform, link]}
                <div class="link-item">
                  <span class="platform">{platform}</span>
                  <a href={link} target="_blank" class="link">{link.substring(0, 40)}...</a>
                </div>
              {/each}
            </div>
          </div>

          <div class="section">
            <h4 class="section-title">Poin Penjualan</h4>
            <ul class="selling-points">
              {#each activeProduct.selling_points || [] as point}
                <li>{point}</li>
              {/each}
            </ul>
          </div>

          {#if activeProduct.compliance_notes}
            <div class="section">
              <h4 class="section-title">Catatan Compliance</h4>
              <p class="compliance-note">{activeProduct.compliance_notes}</p>
            </div>
          {/if}
        {:else}
          <p class="muted">Belum ada produk aktif</p>
        {/if}
      </section>

      <!-- Product Queue Section -->
      <section class="product-card queue">
        <div class="card-header">
          <h3 class="card-title">Antrian Produk</h3>
          <span class="badge badge-count">{queuedProducts.length}</span>
        </div>
        <div class="queue-list">
          {#each queuedProducts as product}
            <div class="queue-item">
              <div class="queue-info">
                <div class="queue-name">{product.name}</div>
                <div class="queue-price">{product.price_formatted}</div>
                <div class="queue-commission">{product.commission_rate}%</div>
              </div>
              <button class="btn btn-switch" onclick={() => handleSwitchProduct(product.id)}>Ganti</button>
            </div>
          {:else}
            <p class="muted">Tidak ada produk dalam antrian</p>
          {/each}
        </div>
      </section>
    </div>
  {/if}
</div>

<style>
  .panel { padding: 4px 0; }
  .panel-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  .panel-title { font-size: 22px; font-weight: 800; margin: 0 0 6px; }
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; }
  .products-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
  .product-card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 20px; }
  .product-card.active { border-left: 4px solid var(--accent); }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .card-title { font-size: 16px; font-weight: 700; margin: 0; }
  .badge { padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
  .badge-active { background: var(--success-bg); color: var(--success-color); }
  .badge-count { background: var(--neutral-bg); color: var(--text-secondary); }
  .product-info { margin-bottom: 20px; }
  .product-name { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
  .product-price { font-size: 24px; font-weight: 800; color: var(--accent); margin-bottom: 4px; }
  .product-category { font-size: 12px; color: var(--muted); text-transform: uppercase; }
  .section { margin-bottom: 20px; }
  .section-title { font-size: 12px; color: var(--muted); text-transform: uppercase; margin-bottom: 10px; font-weight: 700; }
  .commission-rate { font-size: 28px; font-weight: 800; color: var(--success-color); }
  .links-list { display: flex; flex-direction: column; gap: 8px; }
  .link-item { display: flex; gap: 12px; align-items: center; padding: 8px; background: rgba(255,255,255,.02); border-radius: 4px; }
  .platform { font-size: 12px; font-weight: 700; text-transform: uppercase; min-width: 60px; }
  .link { font-size: 12px; color: var(--accent); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .link:hover { text-decoration: underline; }
  .selling-points { margin: 0; padding-left: 20px; }
  .selling-points li { margin-bottom: 6px; font-size: 14px; }
  .compliance-note { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
  .queue-list { display: flex; flex-direction: column; gap: 10px; }
  .queue-item { padding: 12px; background: rgba(255,255,255,.02); border-radius: 4px; border: 1px solid rgba(255,255,255,.05); display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .queue-info { flex: 1; }
  .queue-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
  .queue-price { font-size: 16px; font-weight: 700; color: var(--accent); margin-bottom: 2px; }
  .queue-commission { font-size: 12px; color: var(--success-color); }
  .btn { padding: 8px 16px; border: 1px solid var(--border); border-radius: var(--rsm); cursor: pointer; font-weight: 700; font-family: inherit; font-size: 12px; }
  .btn-ghost { background: rgba(255,255,255,.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-switch { background: var(--accent); color: #000; border: none; }
  .btn-switch:hover { opacity: 0.9; }
  .muted { color: var(--muted); font-style: italic; }
  .error { color: var(--error-color); }
  @media (max-width: 1024px) { .products-grid { grid-template-columns: 1fr; } }
</style>
