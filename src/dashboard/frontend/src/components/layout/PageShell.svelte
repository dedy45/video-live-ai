<script lang="ts">
  import OverviewPanel from '../panels/OverviewPanel.svelte';
  import OpsSummaryPanel from '../panels/OpsSummaryPanel.svelte';
  import VoicePanel from '../panels/VoicePanel.svelte';
  import ReadinessPanel from '../panels/ReadinessPanel.svelte';
  import EnginePanel from '../panels/EnginePanel.svelte';
  import PreviewPanel from '../panels/PreviewPanel.svelte';
  import StreamPanel from '../panels/StreamPanel.svelte';
  import CommercePanel from '../panels/CommercePanel.svelte';
  import MonitorPanel from '../panels/MonitorPanel.svelte';
  import IncidentsPanel from '../panels/IncidentsPanel.svelte';
  import DiagnosticsPanel from '../panels/DiagnosticsPanel.svelte';
  import ValidationPanel from '../panels/ValidationPanel.svelte';

  interface Props {
    activeTab: string;
  }

  let { activeTab }: Props = $props();
</script>

<main class="page-shell">
  {#if activeTab === 'Overview'}
    <div class="overview-stack">
      <OpsSummaryPanel />
      <OverviewPanel />
    </div>
  {:else if activeTab === 'Voice'}
    <VoicePanel />
  {:else if activeTab === 'Face Engine'}
    <EnginePanel />
  {:else if activeTab === 'Stream'}
    <StreamPanel />
  {:else if activeTab === 'Commerce'}
    <CommercePanel />
  {:else if activeTab === 'Monitor'}
    <div class="overview-stack">
      <IncidentsPanel />
      <MonitorPanel />
    </div>
  {:else if activeTab === 'Diagnostics'}
    <DiagnosticsPanel />
  {:else if activeTab === 'Validation'}
    <div class="overview-stack">
      <ReadinessPanel />
      <ValidationPanel />
    </div>
  {/if}
</main>

<style>
  .page-shell {
    flex: 1;
    padding: 16px;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
  }
  .overview-stack {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
</style>
