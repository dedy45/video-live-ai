<script lang="ts">
 import LiveConsolePanel from '../components/panels/LiveConsolePanel.svelte';
 import OpsSummaryPanel from '../components/panels/OpsSummaryPanel.svelte';
</script>

<div class="page">
 <div class="page-header">
  <h1 class="page-title">Konsol Live</h1>
  <p class="page-subtitle">Kontrol real-time untuk operasi live streaming AI</p>
 </div>

 <div class="page-grid">
  <LiveConsolePanel />
  <OpsSummaryPanel />
 </div>
</div>

<style>
 .page {
  width: 100%;
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