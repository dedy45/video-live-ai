<script lang="ts">
 import MonitorPanel from '../components/panels/MonitorPanel.svelte';
 import IncidentsPanel from '../components/panels/IncidentsPanel.svelte';
</script>

<div class="page">
 <div class="page-header">
  <h1 class="page-title">Monitor & Insiden</h1>
  <p class="page-subtitle">Pemantauan sistem dan pelacakan insiden</p>
 </div>

 <div class="page-grid">
  <IncidentsPanel />
  <MonitorPanel />
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
