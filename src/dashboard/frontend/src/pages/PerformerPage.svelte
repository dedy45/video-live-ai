<script lang="ts">
 import PerformerPanel from '../components/panels/PerformerPanel.svelte';
</script>

<div class="page">
 <div class="page-header">
  <h1 class="page-title">Suara & Wajah</h1>
  <p class="page-subtitle">Kontrol terpadu untuk sintesis suara dan animasi wajah</p>
 </div>

 <PerformerPanel />
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
