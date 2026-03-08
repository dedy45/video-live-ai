<script lang="ts">
  import Header from './components/layout/Header.svelte';
  import TruthBar from './components/common/TruthBar.svelte';
  import TabNav from './components/layout/TabNav.svelte';
  import PageShell from './components/layout/PageShell.svelte';

  const tabs = [
    'Overview',
    'Readiness',
    'Engine',
    'Preview',
    'Stream',
    'Commerce',
    'Monitor',
    'Diagnostics',
    'Validation',
  ];

  let activeTab = $state('Overview');

  function handleTabChange(tab: string) {
    activeTab = tab;
  }
</script>

<div class="app">
  <Header />
  <TruthBar />
  <TabNav {tabs} {activeTab} onTabChange={handleTabChange} />
  <PageShell {activeTab} />
</div>
