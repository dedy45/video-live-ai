<script lang="ts">
  import { onMount } from 'svelte';
  import {
    addLiveSessionProducts,
    createProduct,
    deleteProduct,
    getLiveSession,
    getProducts,
    setLiveSessionFocus,
    updateProduct,
  } from '../../lib/api';
  import ActionReceipt from '../common/ActionReceipt.svelte';
  import type { ActionReceipt as ReceiptType } from '../../lib/stores/actions';
  import type { LiveSessionSummary, Product, SessionProduct } from '../../lib/types';

  let products = $state<Product[]>([]);
  let liveSession = $state<LiveSessionSummary | null>(null);
  let loading = $state(true);
  let error = $state('');
  let receipt = $state<ReceiptType | null>(null);
  let editingId = $state<number | null>(null);

  let formName = $state('');
  let formPrice = $state('');
  let formCategory = $state('general');
  let formCommissionRate = $state('');
  let formTiktokLink = $state('');
  let formShopeeLink = $state('');
  let formSellingPoints = $state('');
  let formComplianceNotes = $state('');

  function resetForm() {
    editingId = null;
    formName = '';
    formPrice = '';
    formCategory = 'general';
    formCommissionRate = '';
    formTiktokLink = '';
    formShopeeLink = '';
    formSellingPoints = '';
    formComplianceNotes = '';
  }

  function toReceipt(action: string, status: 'success' | 'error', message: string) {
    receipt = { action, status, message, timestamp: Date.now() };
  }

  async function loadData() {
    loading = true;
    try {
      const [nextProducts, nextLiveSession] = await Promise.all([
        getProducts(),
        getLiveSession(),
      ]);
      products = nextProducts;
      liveSession = nextLiveSession;
      error = '';
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  const sessionProducts = $derived.by(() => liveSession?.products || []);
  const activeProduct = $derived.by(() => {
    const focusId = liveSession?.state?.current_focus_product_id;
    if (focusId) {
      const fromCatalog = products.find((product) => product.id === focusId);
      if (fromCatalog) return fromCatalog;
    }
    const firstSessionProduct = sessionProducts[0];
    if (firstSessionProduct) return firstSessionProduct.product;
    return products[0] || null;
  });
  const queuedSessionProducts = $derived.by(() => {
    const focusId = liveSession?.state?.current_focus_product_id;
    return sessionProducts.filter((item) => item.product_id !== focusId);
  });

  function hydrateForm(product: Product) {
    editingId = product.id;
    formName = product.name;
    formPrice = String(product.price || '');
    formCategory = product.category || 'general';
    formCommissionRate = String(product.commission_rate || '');
    formTiktokLink = product.affiliate_links?.tiktok || '';
    formShopeeLink = product.affiliate_links?.shopee || '';
    formSellingPoints = (product.selling_points || []).join(', ');
    formComplianceNotes = product.compliance_notes || '';
  }

  function buildPayload() {
    return {
      name: formName.trim(),
      price: Number(formPrice || 0),
      category: formCategory.trim() || 'general',
      commission_rate: Number(formCommissionRate || 0),
      affiliate_links: {
        ...(formTiktokLink.trim() ? { tiktok: formTiktokLink.trim() } : {}),
        ...(formShopeeLink.trim() ? { shopee: formShopeeLink.trim() } : {}),
      },
      selling_points: formSellingPoints
        .split(',')
        .map((point) => point.trim())
        .filter(Boolean),
      compliance_notes: formComplianceNotes.trim(),
    };
  }

  async function handleSaveProduct() {
    receipt = null;
    try {
      const payload = buildPayload();
      if (editingId !== null) {
        await updateProduct(editingId, payload);
        toReceipt('product.update', 'success', `Produk ${payload.name} diperbarui.`);
      } else {
        await createProduct(payload);
        toReceipt('product.create', 'success', `Produk ${payload.name} disimpan.`);
      }
      resetForm();
      await loadData();
    } catch (e: any) {
      toReceipt('product.save', 'error', e.message || 'Gagal menyimpan produk');
    }
  }

  async function handleDeleteProduct(productId: number) {
    receipt = null;
    try {
      await deleteProduct(productId);
      if (editingId === productId) resetForm();
      toReceipt('product.delete', 'success', `Produk #${productId} dihapus.`);
      await loadData();
    } catch (e: any) {
      toReceipt('product.delete', 'error', e.message || 'Gagal menghapus produk');
    }
  }

  async function handleAddToSession(productId: number) {
    receipt = null;
    try {
      await addLiveSessionProducts({ product_ids: [productId] });
      toReceipt('session.products.add', 'success', `Produk #${productId} dimasukkan ke sesi live.`);
      await loadData();
    } catch (e: any) {
      toReceipt('session.products.add', 'error', e.message || 'Gagal memasukkan produk ke sesi');
    }
  }

  async function handleSetFocus(item: SessionProduct) {
    receipt = null;
    try {
      await setLiveSessionFocus({ session_product_id: item.id });
      toReceipt('session.focus', 'success', `Fokus dipindah ke ${item.product.name}.`);
      await loadData();
    } catch (e: any) {
      toReceipt('session.focus', 'error', e.message || 'Gagal mengganti fokus');
    }
  }

  onMount(loadData);
</script>

<div class="panel" data-testid="products-offers-panel">
  <div class="panel-header">
    <div>
      <h2 class="panel-title">Produk & Penawaran</h2>
      <p class="panel-subtitle">Dashboard ini sekarang jadi source of truth untuk katalog produk, session pool, komisi, dan compliance notes.</p>
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
      <section class="product-card active">
        <div class="card-header">
          <h3 class="card-title">Produk Aktif</h3>
          <span class="badge badge-active">{liveSession?.session ? 'SESSION LIVE' : 'CATALOG'}</span>
        </div>
        {#if activeProduct}
          <div class="product-info">
            <div class="product-name">{activeProduct.name}</div>
            <div class="product-price">{activeProduct.price_formatted}</div>
            <div class="product-category">{activeProduct.category}</div>
          </div>

          <div class="section">
            <h4 class="section-title">Komisi</h4>
            <div class="commission-rate">{activeProduct.commission_rate || 0}%</div>
          </div>

          <div class="section">
            <h4 class="section-title">Link Affiliate</h4>
            <div class="links-list">
              {#each Object.entries(activeProduct.affiliate_links || {}) as [platform, link]}
                <div class="link-item">
                  <span class="platform">{platform}</span>
                  <a href={link} target="_blank" rel="noreferrer" class="link">{String(link).substring(0, 40)}...</a>
                </div>
              {:else}
                <p class="muted">Belum ada link affiliate.</p>
              {/each}
            </div>
          </div>

          <div class="section">
            <h4 class="section-title">Poin Penjualan</h4>
            <ul class="selling-points">
              {#each activeProduct.selling_points || [] as point}
                <li>{point}</li>
              {:else}
                <li>Tambahkan selling points dari form produk.</li>
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
          <p class="muted">Belum ada produk aktif.</p>
        {/if}
      </section>

      <section class="product-card queue">
        <div class="card-header">
          <h3 class="card-title">Session Pool</h3>
          <span class="badge badge-count">{sessionProducts.length}</span>
        </div>
        {#if liveSession?.session}
          <p class="meta-copy">
            Fokus saat ini: <strong>{activeProduct?.name || 'belum dipilih'}</strong> · Mode <strong>{liveSession?.state?.current_mode || 'unknown'}</strong>
          </p>
        {:else}
          <p class="meta-copy">Belum ada sesi live aktif. Produk tetap bisa disiapkan dari katalog.</p>
        {/if}
        <div class="queue-list">
          {#each queuedSessionProducts as item}
            <div class="queue-item">
              <div class="queue-info">
                <div class="queue-name">{item.product.name}</div>
                <div class="queue-price">{item.product.price_formatted}</div>
                <div class="queue-commission">{item.product.commission_rate || 0}% komisi</div>
              </div>
              <button class="btn btn-switch" onclick={() => handleSetFocus(item)}>Fokuskan</button>
            </div>
          {:else}
            <p class="muted">Belum ada produk lain dalam session pool.</p>
          {/each}
        </div>
      </section>
    </div>

    <div class="bottom-grid">
      <section class="product-card form-card">
        <div class="card-header">
          <h3 class="card-title">Form Produk</h3>
          {#if editingId !== null}
            <button class="btn btn-ghost btn-sm" onclick={resetForm}>Batal Edit</button>
          {/if}
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Nama Produk</span>
            <input bind:value={formName} placeholder="Nama produk live" />
          </label>
          <label class="field">
            <span>Harga</span>
            <input bind:value={formPrice} inputmode="numeric" placeholder="89000" />
          </label>
          <label class="field">
            <span>Kategori</span>
            <input bind:value={formCategory} placeholder="beauty / electronics / fashion" />
          </label>
          <label class="field">
            <span>Komisi (%)</span>
            <input bind:value={formCommissionRate} inputmode="decimal" placeholder="12.5" />
          </label>
          <label class="field">
            <span>Link TikTok</span>
            <input bind:value={formTiktokLink} placeholder="https://shop.tiktok.com/..." />
          </label>
          <label class="field">
            <span>Link Shopee</span>
            <input bind:value={formShopeeLink} placeholder="https://shopee.co.id/..." />
          </label>
          <label class="field span-2">
            <span>Selling Points</span>
            <textarea bind:value={formSellingPoints} rows="3" placeholder="ringan, tahan lama, cocok untuk daily use"></textarea>
          </label>
          <label class="field span-2">
            <span>Compliance Notes</span>
            <textarea bind:value={formComplianceNotes} rows="3" placeholder="Larangan klaim, disclaimer, instruksi aman"></textarea>
          </label>
        </div>
        <div class="form-actions">
          <button class="btn btn-switch" onclick={handleSaveProduct}>Simpan Produk</button>
        </div>
      </section>

      <section class="product-card catalog-card">
        <div class="card-header">
          <h3 class="card-title">Katalog Produk</h3>
          <span class="badge badge-count">{products.length}</span>
        </div>
        <div class="catalog-list">
          {#each products as product}
            <div class="catalog-item">
              <div class="catalog-copy">
                <div class="queue-name">{product.name}</div>
                <div class="queue-price">{product.price_formatted}</div>
                <div class="queue-commission">{product.commission_rate || 0}% komisi · {product.category}</div>
              </div>
              <div class="catalog-actions">
                <button class="btn btn-ghost btn-sm" onclick={() => hydrateForm(product)}>Edit</button>
                <button class="btn btn-ghost btn-sm" onclick={() => handleAddToSession(product.id)}>Masukkan ke Sesi</button>
                <button class="btn btn-danger btn-sm" onclick={() => handleDeleteProduct(product.id)}>Hapus</button>
              </div>
            </div>
          {:else}
            <p class="muted">Belum ada produk di katalog.</p>
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
  .panel-subtitle { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }
  .products-grid, .bottom-grid { display: grid; gap: 16px; }
  .products-grid { grid-template-columns: minmax(0, 1.4fr) minmax(320px, 1fr); }
  .bottom-grid { grid-template-columns: minmax(340px, 1fr) minmax(0, 1.4fr); margin-top: 16px; }
  .product-card { background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); padding: 20px; }
  .product-card.active { border-left: 4px solid var(--accent); }
  .card-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
  .card-title { font-size: 16px; font-weight: 700; margin: 0; }
  .badge { padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
  .badge-active { background: var(--success-bg); color: var(--success-color); }
  .badge-count { background: var(--neutral-bg); color: var(--text-secondary); }
  .product-info { margin-bottom: 20px; }
  .product-name { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
  .product-price, .queue-price { font-size: 22px; font-weight: 800; color: var(--accent); margin-bottom: 4px; }
  .product-category { font-size: 12px; color: var(--muted); text-transform: uppercase; }
  .section { margin-bottom: 20px; }
  .section-title { font-size: 12px; color: var(--muted); text-transform: uppercase; margin-bottom: 10px; font-weight: 700; }
  .commission-rate { font-size: 28px; font-weight: 800; color: var(--success-color); }
  .links-list, .queue-list, .catalog-list { display: flex; flex-direction: column; gap: 8px; }
  .link-item, .queue-item, .catalog-item { display: flex; gap: 12px; align-items: center; padding: 10px 12px; background: rgba(255,255,255,.02); border-radius: 8px; border: 1px solid rgba(255,255,255,.05); }
  .platform { font-size: 12px; font-weight: 700; text-transform: uppercase; min-width: 60px; }
  .link { font-size: 12px; color: var(--accent); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .selling-points { margin: 0; padding-left: 20px; }
  .selling-points li { margin-bottom: 6px; font-size: 14px; }
  .compliance-note, .meta-copy { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
  .queue-info, .catalog-copy { flex: 1; min-width: 0; }
  .queue-name { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
  .queue-commission { font-size: 12px; color: var(--success-color); }
  .catalog-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .field { display: grid; gap: 6px; font-size: 12px; color: var(--muted); }
  .field span { font-weight: 700; color: var(--text); }
  .field input, .field textarea { padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--rsm); background: rgba(255,255,255,.03); color: var(--text); font-family: inherit; font-size: 14px; }
  .field textarea { resize: vertical; }
  .span-2 { grid-column: span 2; }
  .form-actions { margin-top: 14px; display: flex; justify-content: flex-end; }
  .btn { padding: 8px 14px; border: 1px solid var(--border); border-radius: var(--rsm); cursor: pointer; font-weight: 700; font-family: inherit; font-size: 12px; }
  .btn-ghost { background: rgba(255,255,255,.05); color: var(--text); }
  .btn-sm { padding: 6px 10px; font-size: 11px; }
  .btn-switch { background: var(--accent); color: #04111f; border: none; }
  .btn-danger { background: rgba(233, 69, 96, 0.14); color: #ff8ea4; border-color: rgba(233, 69, 96, 0.28); }
  .muted { color: var(--muted); font-style: italic; }
  .error { color: var(--error-color); }
  @media (max-width: 1100px) {
    .products-grid, .bottom-grid { grid-template-columns: 1fr; }
    .span-2 { grid-column: span 1; }
  }
</style>
