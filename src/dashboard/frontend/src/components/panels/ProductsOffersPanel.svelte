<script lang="ts">
  import { onMount } from 'svelte';
  import { getProducts, getStatus } from '../../lib/api';

  let products = $state<any[]>([]);
  let currentProduct = $state<any>(null);
  let loading = $state(true);
  let error = $state('');

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
      <h2 class="panel-title">Products & Offers</h2>
      <p class="panel-subtitle">Affiliate product catalog with selling points, commission, and platform links.</p>
    </div>
  </div>

  {#if loading}
    <p class="muted">Loading products...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <div class="products-grid">
      <!-- Active Product Section -->
      <section class="product-card active">
        <div class="card-header">
          <h3 class="card-title">Active Product</h3>
          <span class="badge badge-active">LIVE</span>
        </div>
        {#if activeProduct}
          <div class="product-info">
            <div class="product-name">{activeProduct.name}</div>
            <div class="product-price">{activeProduct.price_formatted}</div>
            <div class="product-category">{activeProduct.category}</div>
          </div>

          <div class="section">
            <h4 class="section-title">Commission</h4>
            <div class="commission-rate">{activeProduct.commission_rate}%</div>
          </div>

          <div class="section">
            <h4 class="section-title">Affiliate Links</h4>
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
            <h4 class="section-title">Selling Points</h4>
            <ul class="selling-points">
              {#each activeProduct.selling_points || [] as point}
                <li>{point}</li>
              {/each}
            </ul>
          </div>

          {#if activeProduct.compliance_notes}
            <div class="section">
              <h4 class="section-title">Compliance</h4>
              <p class="compliance-note">{activeProduct.compliance_notes}</p>
            </div>
          {/if}
        {:else}
          <p class="muted">No active product</p>
        {/if}
      </section>

      <!-- Product Queue Section -->
      <section class="product-card queue">
        <div class="card-header">
          <h3 class="card-title">Product Queue</h3>
          <span class="badge badge-count">{queuedProducts.length}</span>
        </div>
        <div class="queue-list">
          {#each queuedProducts as product}
            <div class="queue-item">
              <div class="queue-name">{product.name}</div>
              <div class="queue-price">{product.price_formatted}</div>
              <div class="queue-commission">{product.commission_rate}%</div>
            </div>
          {:else}
            <p class="muted">No queued products</p>
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
  .queue-item { padding: 12px; background: rgba(255,255,255,.02); border-radius: 4px; border: 1px solid rgba(255,255,255,.05); }
  .queue-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
  .queue-price { font-size: 16px; font-weight: 700; color: var(--accent); margin-bottom: 2px; }
  .queue-commission { font-size: 12px; color: var(--success-color); }
  .muted { color: var(--muted); font-style: italic; }
  .error { color: var(--error-color); }
  @media (max-width: 1024px) { .products-grid { grid-template-columns: 1fr; } }
</style>
