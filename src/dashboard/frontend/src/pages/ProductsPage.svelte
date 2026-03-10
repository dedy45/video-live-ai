<script lang="ts">
 import ProductsOffersPanel from '../components/panels/ProductsOffersPanel.svelte';
</script>

<div class="page">
 <div class="page-header">
  <h1 class="page-title">Produk & Penawaran</h1>
  <p class="page-subtitle">Katalog produk affiliate dengan poin penjualan, komisi, dan link platform</p>
 </div>

 <ProductsOffersPanel />
</div>

<style>
 .page {
  padding: 20px;
 }

 .page-header {
  margin-bottom: 24px;
 }

 .page-title {
  font-size: 28px;
  font-weight: 800;
  margin: 0 0 8px;
  color: var(--text);
 }

 .page-subtitle {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
 }
</style>
