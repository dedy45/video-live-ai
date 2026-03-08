<script lang="ts">
  import OverviewPanel from '../panels/OverviewPanel.svelte';
  import ReadinessPanel from '../panels/ReadinessPanel.svelte';
  import EnginePanel from '../panels/EnginePanel.svelte';
  import PreviewPanel from '../panels/PreviewPanel.svelte';
  import StreamPanel from '../panels/StreamPanel.svelte';
  import CommercePanel from '../panels/CommercePanel.svelte';
  import MonitorPanel from '../panels/MonitorPanel.svelte';
  import DiagnosticsPanel from '../panels/DiagnosticsPanel.svelte';
  import ValidationPanel from '../panels/ValidationPanel.svelte';

  interface Props {
    activeTab: string;
  }

  let { activeTab }: Props = $props();
</script>

<main class="page-shell">
  {#if activeTab === 'Overview'}
    <OverviewPanel />
  {:else if activeTab === 'Readiness'}
    <ReadinessPanel />
  {:else if activeTab === 'Engine'}
    <EnginePanel />
  {:else if activeTab === 'Preview'}
    <PreviewPanel />
  {:else if activeTab === 'Stream'}
    <StreamPanel />
  {:else if activeTab === 'Commerce'}
    <CommercePanel />
  {:else if activeTab === 'Monitor'}
    <MonitorPanel />
  {:else if activeTab === 'Diagnostics'}
    <DiagnosticsPanel />
  {:else if activeTab === 'Validation'}
    <ValidationPanel />
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
</style>
