<script lang="ts">
 import { onMount } from 'svelte';
 import Card from '../components/common/Card.svelte';
 import ReadinessPanel from '../components/panels/ReadinessPanel.svelte';
 import ValidationPanel from '../components/panels/ValidationPanel.svelte';
 import DiagnosticsPanel from '../components/panels/DiagnosticsPanel.svelte';
 import { getRuntimeTruth, getOpsSummary } from '../lib/api';
 import type { OpsSummary, RuntimeTruth } from '../lib/types';

 let truth = $state<RuntimeTruth | null>(null);
 let opsSummary = $state<OpsSummary | null>(null);
 let loading = $state(true);
 let error = $state('');
 let refreshKey = $state(0);

 function deriveOrigin(nextTruth: RuntimeTruth | null): string {
  if (!nextTruth?.provenance) return 'unknown';
  const values = Object.values(nextTruth.provenance);
  if (values.some((value) => value === 'real_live')) return 'real_live';
  if (values.some((value) => value === 'real_local')) return 'real_local';
  if (values.every((value) => value === 'mock')) return 'mock';
  if (values.every((value) => value === 'derived')) return 'derived';
  return 'mixed';
 }

 async function loadSummary() {
  loading = true;
  error = '';
  try {
   const [nextTruth, nextOpsSummary] = await Promise.all([
    getRuntimeTruth() as Promise<RuntimeTruth>,
    getOpsSummary() as Promise<OpsSummary>,
   ]);
   truth = nextTruth;
   opsSummary = nextOpsSummary;
  } catch (nextError: any) {
   error = nextError.message || 'Failed to load setup summary';
  } finally {
   loading = false;
  }
 }

 function refreshAll() {
  refreshKey += 1;
  void loadSummary();
 }

 const environmentRows = $derived([
  { label: 'Host', value: truth?.host?.name || 'unknown' },
  { label: 'Role', value: truth?.host?.role || 'unknown' },
  { label: 'Deploy', value: truth?.deployment_mode || opsSummary?.deployment_mode || 'unknown' },
  { label: 'Origin', value: deriveOrigin(truth) },
  { label: 'Voice', value: truth?.voice_runtime_mode || 'unknown' },
  { label: 'Face', value: truth?.face_runtime_mode || 'unknown' },
  { label: 'Stream', value: truth?.stream_runtime_mode || 'unknown' },
  { label: 'Incidents', value: String(opsSummary?.incident_summary?.open_count ?? 0) },
 ]);

 onMount(() => {
  void loadSummary();
 });
</script>

<div class="page">
 <div class="page-header">
  <div>
   <h1 class="page-title">Setup & Validasi Sistem</h1>
   <p class="page-subtitle">Gate kesiapan operator sebelum produk, performer, dan stream dijalankan di mode production.</p>
  </div>
  <button class="refresh-btn" onclick={refreshAll} disabled={loading}>Refresh</button>
 </div>

 {#if error}
  <div class="error-banner" role="alert">{error}</div>
 {/if}

 {#if loading}
  <div class="loading-panel">Memuat setup summary...</div>
 {:else}
  <div class="hero-grid">
   <section class="hero-card">
    <div class="hero-label">System readiness</div>
    <div class="hero-value">{opsSummary?.overall_status?.toUpperCase() || 'UNKNOWN'}</div>
    <div class="hero-copy">Voice {opsSummary?.voice_status || 'unknown'} · Face {opsSummary?.face_status || 'unknown'} · Stream {opsSummary?.stream_status || 'unknown'}</div>
   </section>
   <section class="hero-card">
    <div class="hero-label">Environment</div>
    <div class="hero-value">Production-first</div>
    <div class="hero-copy">Reload selalu fetch fresh state. Tidak ada restore dari browser cache.</div>
   </section>
  </div>

  <Card title="Environment" size="lg">
   <div class="env-grid">
    {#each environmentRows as row}
     <div class="env-row">
      <span class="env-label">{row.label}</span>
      <strong class="env-value">{row.value}</strong>
     </div>
    {/each}
   </div>
   <div class="resource-strip">
    <span class="resource-chip">CPU {opsSummary?.resource_metrics?.cpu_pct ?? 0}%</span>
    <span class="resource-chip">RAM {opsSummary?.resource_metrics?.ram_pct ?? 0}%</span>
    <span class="resource-chip">Disk {opsSummary?.resource_metrics?.disk_pct ?? 0}%</span>
    <span class="resource-chip">VRAM {opsSummary?.resource_metrics?.vram_pct ?? 'n/a'}%</span>
   </div>
  </Card>

  <div class="panel-grid">
   <Card title="System Readiness" size="lg">
    {#key `readiness-${refreshKey}`}
     <ReadinessPanel />
    {/key}
   </Card>

   <Card title="Validation Gates" size="lg">
    {#key `validation-${refreshKey}`}
     <ValidationPanel />
    {/key}
   </Card>
  </div>

  <details class="developer-tools">
   <summary>Developer Tools</summary>
   <div class="developer-copy">
    Dipakai hanya untuk drill-down teknis. Bukan permukaan operator harian.
   </div>
   {#key `diagnostics-${refreshKey}`}
    <DiagnosticsPanel />
   {/key}
  </details>
 {/if}
</div>

<style>
 .page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
 }
 .page-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
 }
 .page-title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 800;
 }
 .page-subtitle {
  margin: 0;
  color: var(--muted);
  max-width: 760px;
  line-height: 1.5;
 }
 .refresh-btn {
  padding: 10px 16px;
  border-radius: var(--rsm);
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  cursor: pointer;
  font-weight: 700;
 }
 .refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
 }
 .error-banner,
 .loading-panel {
  padding: 14px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background: var(--card);
 }
 .error-banner {
  color: var(--accent);
  border-color: rgba(233, 69, 96, 0.3);
 }
 .hero-grid,
 .panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
 }
 .hero-card {
  padding: 22px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  background:
   radial-gradient(circle at top left, rgba(34, 211, 238, 0.12), transparent 40%),
   linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.01));
 }
 .hero-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--muted);
 }
 .hero-value {
  margin: 10px 0 8px;
  font-size: 32px;
  font-weight: 900;
 }
 .hero-copy {
  color: var(--muted);
  line-height: 1.5;
 }
 .env-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
 }
 .env-row {
  padding: 12px 14px;
  border-radius: var(--rsm);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  gap: 12px;
 }
 .env-label {
  color: var(--muted);
 }
 .env-value {
  color: var(--text);
 }
 .resource-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
 }
 .resource-chip {
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(34, 211, 238, 0.08);
  border: 1px solid rgba(34, 211, 238, 0.18);
  font-size: 12px;
  font-weight: 700;
 }
 .developer-tools {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.02);
  padding: 16px 18px;
 }
 .developer-tools summary {
  cursor: pointer;
  font-weight: 700;
 }
 .developer-copy {
  margin: 12px 0 16px;
  color: var(--muted);
  font-size: 13px;
 }
 @media (max-width: 768px) {
  .page {
   padding: 16px;
  }
  .page-header {
   flex-direction: column;
  }
  .refresh-btn {
   width: 100%;
  }
  .page-title {
   font-size: 28px;
  }
 }
</style>
