<script lang="ts">
 import ValidationPanel from '../components/panels/ValidationPanel.svelte';
 import ReadinessPanel from '../components/panels/ReadinessPanel.svelte';
</script>

<div class="page">
 <div class="page-header">
  <h1 class="page-title">Validasi & Kesiapan</h1>
  <p class="page-subtitle">Pemeriksaan validasi sistem dan status kesiapan deployment</p>
 </div>

 <div class="page-grid">
  <ReadinessPanel />
  <ValidationPanel />
 </div>
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

 .page-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
 }
</style>
